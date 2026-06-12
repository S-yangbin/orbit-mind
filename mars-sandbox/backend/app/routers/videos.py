"""Video management API routes."""
import os
import uuid
import logging
import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from ..config import settings
from ..utils.timezone import beijing_now
from ..database import get_db
from ..auth import get_current_user
from ..models import Video, VideoSegment, SegmentNote, SegmentProgress
from ..schemas import (
    VideoResponse, VideoListResponse, VideoUploadResponse,
    VideoSegmentResponse, SegmentNoteResponse, SegmentProgressResponse,
    SegmentCreate, SegmentUpdate, SegmentNoteCreate, SegmentProgressUpdate,
)
from ..services.video_processor import start_async_processing
from ..utils.oss_url import generate_signed_video_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["videos"])

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"}


def _video_to_response(video: Video) -> dict:
    """Convert Video ORM to response dict."""
    total_segments = len(video.segments) if video.segments else 0
    mastered = sum(1 for s in (video.segments or []) if s.progress and s.progress.mastered)
    return {
        **VideoResponse.from_orm(video).dict(),
        "segment_count": total_segments,
        "mastered_count": mastered,
        "oss_url": generate_signed_video_url(video.file_path) or None,
    }


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload a video file to OSS storage."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate extension
    ext = Path(file.filename or "video.mp4").suffix.lower()
    if ext not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}. Supported: {', '.join(VIDEO_EXTENSIONS)}")

    # Ensure directory exists
    os.makedirs(settings.VIDEO_ROOT, exist_ok=True)

    # Generate unique filename to avoid collisions
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.VIDEO_ROOT, safe_name)

    # Save file
    file_size = 0
    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            f.write(chunk)
            file_size += len(chunk)

    # Create DB record
    video = Video(
        title=title,
        filename=file.filename or safe_name,
        file_path=safe_name,  # relative path for OSS
        file_size=file_size,
        status="pending",
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    logger.info("Video uploaded: id=%s title=%s size=%s", video.id, title, file_size)

    return VideoUploadResponse(
        id=video.id,
        title=video.title,
        filename=video.filename,
        file_size=video.file_size,
        status=video.status,
        message="Video uploaded successfully. Trigger processing to extract audio and analyze segments.",
    )


@router.get("", response_model=VideoListResponse)
async def list_videos(
    request: Request,
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
):
    """List all videos with optional filtering."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    query = db.query(Video).options(
        joinedload(Video.segments).joinedload(VideoSegment.progress)
    )

    if q:
        query = query.filter(Video.title.contains(q))
    if status:
        query = query.filter(Video.status == status)

    # Sort
    sort_col = getattr(Video, sort, Video.created_at)
    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return VideoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_video_to_response(v) for v in items],
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    request: Request,
    video_id: int,
    db: Session = Depends(get_db),
):
    """Get a single video with all segments, notes and progress."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    video = db.query(Video).options(
        joinedload(Video.segments)
        .joinedload(VideoSegment.notes),
        joinedload(Video.segments)
        .joinedload(VideoSegment.progress),
    ).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return _video_to_response(video)


@router.post("/{video_id}/process")
async def process_video_endpoint(
    request: Request,
    video_id: int,
    db: Session = Depends(get_db),
):
    """Trigger async video processing (audio extraction + ASR + LLM segment analysis)."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status == "processing":
        raise HTTPException(status_code=400, detail="Video is already being processed")

    video.status = "pending"
    db.commit()

    start_async_processing(video_id)

    return {"message": "Processing started", "video_id": video_id}


@router.get("/{video_id}/stream")
async def stream_video(
    request: Request,
    video_id: int,
    db: Session = Depends(get_db),
):
    """Stream video file with Range header support for seeking."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = os.path.join(settings.VIDEO_ROOT, video.file_path)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    file_size = os.path.getsize(video_path)
    content_type, _ = mimetypes.guess_type(video_path)
    if not content_type:
        content_type = "video/mp4"

    range_header = request.headers.get("range")

    if range_header:
        # Parse Range header
        start, end = 0, file_size - 1
        range_match = range_header.replace("bytes=", "").split("-")
        if range_match[0]:
            start = int(range_match[0])
        if len(range_match) > 1 and range_match[1]:
            end = int(range_match[1])
        else:
            end = file_size - 1

        chunk_size = end - start + 1

        async def ranged_file_iterator():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    buf = f.read(min(1024 * 1024, remaining))
                    if not buf:
                        break
                    remaining -= len(buf)
                    yield buf

        return StreamingResponse(
            ranged_file_iterator(),
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": content_type,
            },
        )

    # Full file response
    return FileResponse(video_path, media_type=content_type)


# --- Segment CRUD ---

@router.post("/{video_id}/segments", response_model=VideoSegmentResponse)
async def create_segment(
    request: Request,
    video_id: int,
    segment: SegmentCreate,
    db: Session = Depends(get_db),
):
    """Manually add a new segment to a video."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    seg = VideoSegment(
        video_id=video_id,
        title=segment.title,
        segment_type=segment.segment_type,
        start_time=segment.start_time,
        end_time=segment.end_time,
        transcription=segment.transcription,
        sort_order=segment.sort_order,
    )
    db.add(seg)
    db.flush()

    # Create progress record
    progress = SegmentProgress(segment_id=seg.id)
    db.add(progress)

    db.commit()
    db.refresh(seg)

    return VideoSegmentResponse.from_orm(seg)


@router.put("/segments/{segment_id}", response_model=VideoSegmentResponse)
async def update_segment(
    request: Request,
    segment_id: int,
    data: SegmentUpdate,
    db: Session = Depends(get_db),
):
    """Edit a segment's title, time range, or type."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    seg = db.query(VideoSegment).filter(VideoSegment.id == segment_id).first()
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")

    if data.title is not None:
        seg.title = data.title
    if data.segment_type is not None:
        seg.segment_type = data.segment_type
    if data.start_time is not None:
        seg.start_time = data.start_time
    if data.end_time is not None:
        seg.end_time = data.end_time
    if data.transcription is not None:
        seg.transcription = data.transcription
    if data.sort_order is not None:
        seg.sort_order = data.sort_order

    db.commit()
    db.refresh(seg)

    return VideoSegmentResponse.from_orm(seg)


@router.delete("/segments/{segment_id}")
async def delete_segment(
    request: Request,
    segment_id: int,
    db: Session = Depends(get_db),
):
    """Delete a segment."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    seg = db.query(VideoSegment).filter(VideoSegment.id == segment_id).first()
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")

    db.delete(seg)
    db.commit()

    return {"message": "Segment deleted"}


# --- Notes ---

@router.post("/segments/{segment_id}/notes", response_model=SegmentNoteResponse)
async def upsert_note(
    request: Request,
    segment_id: int,
    note_data: SegmentNoteCreate,
    db: Session = Depends(get_db),
):
    """Add or update a note for a segment. Also persists to OSS as markdown file."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    seg = db.query(VideoSegment).filter(VideoSegment.id == segment_id).first()
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")

    # Update or create note (one note per segment for simplicity)
    note = db.query(SegmentNote).filter(SegmentNote.segment_id == segment_id).first()
    if note:
        note.content = note_data.content
    else:
        note = SegmentNote(segment_id=segment_id, content=note_data.content)
        db.add(note)
        db.flush()

    # Persist to OSS markdown file
    video_id = seg.video_id
    notes_dir = os.path.join(settings.VIDEO_NOTES_DIR, str(video_id))
    os.makedirs(notes_dir, exist_ok=True)
    note_path = os.path.join(notes_dir, f"{segment_id}.md")
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(f"# {seg.title}\n\n")
        f.write(f"*Segment: {seg.start_time}s - {seg.end_time}s*\n\n")
        f.write(note_data.content)

    note.note_path = os.path.join(str(video_id), f"{segment_id}.md")
    db.commit()
    db.refresh(note)

    return SegmentNoteResponse.from_orm(note)


# --- Progress ---

@router.put("/segments/{segment_id}/progress", response_model=SegmentProgressResponse)
async def update_progress(
    request: Request,
    segment_id: int,
    data: SegmentProgressUpdate,
    db: Session = Depends(get_db),
):
    """Update learning progress for a segment."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    progress = db.query(SegmentProgress).filter(SegmentProgress.segment_id == segment_id).first()
    if not progress:
        # Auto-create if missing
        progress = SegmentProgress(segment_id=segment_id)
        db.add(progress)
        db.flush()

    if data.mastered is not None:
        progress.mastered = data.mastered
    if data.loop_count is not None:
        progress.loop_count = data.loop_count
    if data.last_practiced_at is not None:
        progress.last_practiced_at = data.last_practiced_at
    else:
        progress.last_practiced_at = beijing_now()

    db.commit()
    db.refresh(progress)

    return SegmentProgressResponse.from_orm(progress)