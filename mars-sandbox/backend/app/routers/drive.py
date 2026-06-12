"""Cloud drive API routes - STS auth + file metadata CRUD."""
import hmac
import hashlib
import base64
import logging
import os
import time
import urllib.parse
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..auth import get_current_user
from ..models import DriveFile
from ..schemas import (
    DriveFileResponse,
    DriveFileListResponse,
    DriveFileCreate,
    DriveFolderCreate,
    DriveFileMove,
    DriveFileCopy,
    STSTokenResponse,
)
from ..utils.sts_token import get_sts_token, DRIVE_PREFIX

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/drive", tags=["drive"])


# ============================================================
# OSS helper functions
# ============================================================

def _oss_sign_url(method: str, oss_key: str, expires_in: int = 60, content_type: str = "", oss_headers: dict = None) -> tuple:
    """Compute OSS V1 signature and expiry timestamp.

    Returns:
        (url_encoded_signature, expiry_timestamp)
    """
    expires = int(time.time()) + expires_in
    # OSS V1 signature: METHOD\nContent-MD5\nContent-Type\nExpires\nCanonicalizedOSSHeaders\nResource
    canonical_headers = ""
    if oss_headers:
        sorted_headers = sorted((k.lower(), v) for k, v in oss_headers.items() if k.lower().startswith("x-oss-"))
        canonical_headers = "\n".join(f"{k}:{v}" for k, v in sorted_headers) + "\n"
    string_to_sign = f"{method}\n\n{content_type}\n{expires}\n{canonical_headers}/{settings.OSS_BUCKET}/{oss_key}"
    signature_bytes = hmac.new(
        settings.OSS_ACCESS_KEY_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    signature = base64.b64encode(signature_bytes).decode("utf-8")
    return urllib.parse.quote(signature, safe=""), int(expires)


def _oss_signed_url(method: str, oss_key: str, expires_in: int = 60, content_type: str = "", oss_headers: dict = None) -> str:
    """Build a full signed OSS V1 URL for any HTTP method and key."""
    sig, expires = _oss_sign_url(method, oss_key, expires_in, content_type, oss_headers)
    return (
        f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT}"
        f"/{oss_key}"
        f"?OSSAccessKeyId={settings.OSS_ACCESS_KEY_ID}"
        f"&Expires={expires}"
        f"&Signature={sig}"
    )


def _oss_request(method: str, oss_key: str, expires_in: int = 60, oss_headers: dict = None, headers: dict = None, data: bytes = None):
    """Execute an HTTP request against OSS using signed URL.

    Args:
        oss_headers: x-oss-* headers included in the signature.
        headers: Standard HTTP headers (e.g. Range) sent but not signed.
    """
    import urllib.request
    url = _oss_signed_url(method, oss_key, expires_in, oss_headers=oss_headers)
    req = urllib.request.Request(url, method=method, data=data)
    for h in (oss_headers or {}):
        req.add_header(h, oss_headers[h])
    for h in (headers or {}):
        req.add_header(h, headers[h])
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def _oss_copy_object(src_key: str, dst_key: str):
    """Copy an OSS object to a new key using PUT + x-oss-copy-source."""
    copy_source = f"/{settings.OSS_BUCKET}/{src_key}"
    _oss_request("PUT", dst_key, expires_in=120, oss_headers={"x-oss-copy-source": copy_source})


def _oss_list_objects(prefix: str) -> list:
    """List all object keys under a given prefix."""
    import urllib.request
    import xml.etree.ElementTree as ET

    keys = []
    marker = ""
    while True:
        params = {"prefix": prefix, "max-keys": "1000"}
        if marker:
            params["marker"] = marker
        query_string = urllib.parse.urlencode(params)
        # Build signed URL for bucket-level GET listing
        sig, expires = _oss_sign_url("GET", "", expires_in=60)
        url = (
            f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT}"
            f"/?{query_string}"
            f"&OSSAccessKeyId={settings.OSS_ACCESS_KEY_ID}"
            f"&Expires={expires}"
            f"&Signature={sig}"
        )
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()

        root = ET.fromstring(body)
        ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
        for item in root.findall(f"{ns}Contents"):
            key = item.find(f"{ns}Key")
            if key is not None and key.text:
                keys.append(key.text)
        is_truncated = root.find(f"{ns}IsTruncated")
        next_marker = root.find(f"{ns}NextMarker")
        if is_truncated is not None and is_truncated.text == "true" and next_marker is not None:
            marker = next_marker.text
        else:
            break
    return keys


def _build_folder_oss_key(parent_id: Optional[int], foldername: str, db: Session) -> str:
    """Build the OSS key for a folder based on parent path."""
    path_parts = []
    current_id = parent_id
    while current_id is not None:
        parent = db.query(DriveFile).filter(DriveFile.id == current_id).first()
        if parent and parent.is_dir:
            path_parts.insert(0, parent.filename)
            current_id = parent.parent_id
        else:
            break
    return DRIVE_PREFIX + "/".join(path_parts + [foldername]) + "/"


def _get_breadcrumbs(folder_id: Optional[int], db: Session) -> list:
    """Build breadcrumb list from root to the given folder."""
    crumbs = []
    current_id = folder_id
    while current_id is not None:
        folder = db.query(DriveFile).filter(DriveFile.id == current_id).first()
        if folder and folder.is_dir:
            crumbs.insert(0, {"id": folder.id, "filename": folder.filename})
            current_id = folder.parent_id
        else:
            break
    return crumbs


def _get_all_children(folder_id: int, db: Session) -> list:
    """Recursively get all child IDs (files and sub-folders) of a folder."""
    children = db.query(DriveFile).filter(DriveFile.parent_id == folder_id).all()
    result = list(children)
    for child in children:
        if child.is_dir:
            result.extend(_get_all_children(child.id, db))
    return result


@router.get("/sts-token", response_model=STSTokenResponse)
async def get_sts_credentials(request: Request):
    """Get STS temporary credentials for frontend direct OSS access."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token_data = get_sts_token(duration_seconds=900)
        return STSTokenResponse(**token_data)
    except Exception as e:
        logger.error("Failed to get STS token: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get STS token: {e}")


@router.get("/files", response_model=DriveFileListResponse)
async def list_files(
    request: Request,
    parent_id: Optional[int] = Query(None, description="Parent folder ID (null=root)"),
    q: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
):
    """List cloud drive files with pagination and search, optionally filtered by parent folder."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    query = db.query(DriveFile)

    # Filter by parent folder
    if parent_id is not None:
        query = query.filter(DriveFile.parent_id == parent_id)
    else:
        # When browsing (not searching), show only root items
        if not q:
            query = query.filter(DriveFile.parent_id.is_(None))

    if q:
        query = query.filter(DriveFile.filename.contains(q))

    # Folders first, then files; secondary sort by requested field
    sort_col = getattr(DriveFile, sort, DriveFile.created_at)
    if order == "asc":
        query = query.order_by(DriveFile.is_dir.desc(), sort_col.asc())
    else:
        query = query.order_by(DriveFile.is_dir.desc(), sort_col.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    breadcrumbs = _get_breadcrumbs(parent_id, db) if parent_id else []

    return DriveFileListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[DriveFileResponse.from_orm(f) for f in items],
        breadcrumbs=breadcrumbs,
    )


@router.post("/files", response_model=DriveFileResponse)
async def record_uploaded_file(
    request: Request,
    file_data: DriveFileCreate,
    db: Session = Depends(get_db),
):
    """Record file metadata after frontend uploads to OSS directly."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate oss_key is under clouddisk/ prefix
    if not file_data.oss_key.startswith(DRIVE_PREFIX):
        raise HTTPException(
            status_code=400,
            detail=f"oss_key must start with '{DRIVE_PREFIX}'"
        )

    # Check for duplicate
    existing = db.query(DriveFile).filter(DriveFile.oss_key == file_data.oss_key).first()
    if existing:
        return DriveFileResponse.from_orm(existing)

    drive_file = DriveFile(
        filename=file_data.filename,
        oss_key=file_data.oss_key,
        file_size=file_data.file_size,
        content_type=file_data.content_type,
        uploaded_by=user.get("username", "unknown"),
        parent_id=file_data.parent_id,
    )
    db.add(drive_file)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save file record")
    db.refresh(drive_file)

    logger.info("Drive file recorded: id=%s filename=%s size=%s", drive_file.id, drive_file.filename, drive_file.file_size)
    return DriveFileResponse.from_orm(drive_file)


@router.delete("/files/{file_id}")
async def delete_file(
    request: Request,
    file_id: int,
    db: Session = Depends(get_db),
):
    """Delete a file from OSS and DB."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    drive_file = db.query(DriveFile).filter(DriveFile.id == file_id).first()
    if not drive_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from OSS
    oss_key = drive_file.oss_key
    try:
        _delete_oss_object(oss_key)
        logger.info("Deleted OSS object: %s", oss_key)
    except Exception as e:
        logger.warning("Failed to delete OSS object %s: %s", oss_key, e)

    # Delete from DB
    db.delete(drive_file)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("DB commit failed after OSS delete — OSS/DB inconsistent for file_id=%s oss_key=%s", file_id, oss_key)
        raise HTTPException(status_code=500, detail="Failed to delete file record (OSS object already deleted)")

    logger.info("Drive file deleted: id=%s filename=%s", file_id, drive_file.filename)
    return {"message": "File deleted", "id": file_id}


# ============================================================
# Folder operations
# ============================================================

@router.post("/folders", response_model=DriveFileResponse)
async def create_folder(
    request: Request,
    folder_data: DriveFolderCreate,
    db: Session = Depends(get_db),
):
    """Create a new folder."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate parent exists and is a folder
    if folder_data.parent_id is not None:
        parent = db.query(DriveFile).filter(DriveFile.id == folder_data.parent_id).first()
        if not parent or not parent.is_dir:
            raise HTTPException(status_code=400, detail="Invalid parent folder")

    # Check duplicate name in same parent
    existing = db.query(DriveFile).filter(
        DriveFile.parent_id == folder_data.parent_id,
        DriveFile.filename == folder_data.filename,
        DriveFile.is_dir == 1,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Folder '{folder_data.filename}' already exists")

    oss_key = _build_folder_oss_key(folder_data.parent_id, folder_data.filename, db)

    folder = DriveFile(
        filename=folder_data.filename,
        oss_key=oss_key,
        file_size=0,
        content_type="",
        uploaded_by=user.get("username", "unknown"),
        is_dir=1,
        parent_id=folder_data.parent_id,
    )
    db.add(folder)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create folder")
    db.refresh(folder)

    logger.info("Drive folder created: id=%s name=%s", folder.id, folder.filename)
    return DriveFileResponse.from_orm(folder)


@router.delete("/folders/{folder_id}")
async def delete_folder(
    request: Request,
    folder_id: int,
    db: Session = Depends(get_db),
):
    """Delete a folder and all its contents (files and sub-folders)."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    folder = db.query(DriveFile).filter(DriveFile.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if not folder.is_dir:
        raise HTTPException(status_code=400, detail="Not a folder")

    # Get all children recursively
    children = _get_all_children(folder_id, db)

    # Delete OSS objects for all files (not folders)
    for child in children:
        if not child.is_dir:
            try:
                _delete_oss_object(child.oss_key)
            except Exception as e:
                logger.warning("Failed to delete OSS object %s: %s", child.oss_key, e)

    # DB cascade delete handles children
    db.delete(folder)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("DB commit failed after OSS delete — OSS/DB inconsistent for folder_id=%s", folder_id)
        raise HTTPException(status_code=500, detail="Failed to delete folder record (OSS objects already deleted)")

    logger.info("Drive folder deleted: id=%s name=%s (children=%d)", folder_id, folder.filename, len(children))
    return {"message": "Folder deleted", "id": folder_id, "children_deleted": len(children)}


@router.post("/files/{file_id}/move", response_model=DriveFileResponse)
async def move_file(
    request: Request,
    file_id: int,
    move_data: DriveFileMove,
    db: Session = Depends(get_db),
):
    """Move a file or folder to a target directory. Updates OSS keys recursively for folders."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    item = db.query(DriveFile).filter(DriveFile.id == file_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="File not found")

    # Validate target
    if move_data.target_parent_id is not None:
        target = db.query(DriveFile).filter(DriveFile.id == move_data.target_parent_id).first()
        if not target or not target.is_dir:
            raise HTTPException(status_code=400, detail="Invalid target folder")

    # Prevent moving a folder into itself or its descendants
    if item.is_dir and move_data.target_parent_id is not None:
        descendants = _get_all_children(item.id, db)
        descendant_ids = {d.id for d in descendants}
        if move_data.target_parent_id == item.id or move_data.target_parent_id in descendant_ids:
            raise HTTPException(status_code=400, detail="Cannot move folder into itself or its subfolder")

    # Build new OSS key
    if move_data.target_parent_id is not None:
        target_folder = db.query(DriveFile).filter(DriveFile.id == move_data.target_parent_id).first()
        new_oss_key = target_folder.oss_key + item.filename
        if item.is_dir:
            new_oss_key = target_folder.oss_key + item.filename + "/"
    else:
        new_oss_key = DRIVE_PREFIX + item.filename
        if item.is_dir:
            new_oss_key = DRIVE_PREFIX + item.filename + "/"

    if item.is_dir:
        # Move all children recursively in OSS
        _move_oss_recursive(item, new_oss_key, db)

    elif not item.is_dir:
        # Copy then delete for files
        try:
            _oss_copy_object(item.oss_key, new_oss_key)
            _delete_oss_object(item.oss_key)
        except Exception as e:
            logger.error("OSS move failed: %s", e)
            raise HTTPException(status_code=500, detail=f"OSS move failed: {e}")

    item.oss_key = new_oss_key
    item.parent_id = move_data.target_parent_id
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("DB commit failed after OSS move — OSS/DB inconsistent for file_id=%s", file_id)
        raise HTTPException(status_code=500, detail="Failed to update file record after OSS move")
    db.refresh(item)

    logger.info("Drive item moved: id=%s to parent=%s", file_id, move_data.target_parent_id)
    return DriveFileResponse.from_orm(item)


def _move_oss_recursive(folder: DriveFile, new_folder_key: str, db: Session):
    """Move all OSS objects under old folder prefix to new folder prefix."""
    old_prefix = folder.oss_key
    try:
        keys = _oss_list_objects(old_prefix)
        for key in keys:
            new_key = new_folder_key + key[len(old_prefix):]
            _oss_copy_object(key, new_key)
            _delete_oss_object(key)
    except Exception as e:
        logger.warning("OSS recursive move error: %s", e)

    # Update DB for direct children
    children = db.query(DriveFile).filter(DriveFile.parent_id == folder.id).all()
    for child in children:
        if child.is_dir:
            child_new_key = new_folder_key + child.filename + "/"
            _move_oss_recursive(child, child_new_key, db)
            child.oss_key = child_new_key
        else:
            child_new_key = new_folder_key + child.filename
            child.oss_key = child_new_key


@router.post("/files/{file_id}/copy", response_model=DriveFileResponse)
async def copy_file(
    request: Request,
    file_id: int,
    copy_data: DriveFileCopy,
    db: Session = Depends(get_db),
):
    """Copy a file to a target directory."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    item = db.query(DriveFile).filter(DriveFile.id == file_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    if item.is_dir:
        raise HTTPException(status_code=400, detail="Folder copy not supported, copy files individually")

    # Build new OSS key
    if copy_data.target_parent_id is not None:
        target = db.query(DriveFile).filter(DriveFile.id == copy_data.target_parent_id).first()
        if not target or not target.is_dir:
            raise HTTPException(status_code=400, detail="Invalid target folder")
        new_oss_key = target.oss_key + item.filename
    else:
        new_oss_key = DRIVE_PREFIX + item.filename

    # Handle name collision
    existing = db.query(DriveFile).filter(DriveFile.oss_key == new_oss_key).first()
    if existing:
        # Add suffix
        name, ext = os.path.splitext(item.filename)
        new_oss_key = (DRIVE_PREFIX + (target.oss_key if copy_data.target_parent_id else "") +
                       f"{name}_copy{ext}")

    try:
        _oss_copy_object(item.oss_key, new_oss_key)
    except Exception as e:
        logger.error("OSS copy failed: %s", e)
        raise HTTPException(status_code=500, detail=f"OSS copy failed: {e}")

    new_file = DriveFile(
        filename=os.path.basename(new_oss_key.replace(DRIVE_PREFIX, "")),
        oss_key=new_oss_key,
        file_size=item.file_size,
        content_type=item.content_type,
        uploaded_by=user.get("username", "unknown"),
        is_dir=0,
        parent_id=copy_data.target_parent_id,
    )
    db.add(new_file)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("DB commit failed after OSS copy — orphaned OSS object at %s", new_oss_key)
        raise HTTPException(status_code=500, detail="Failed to save copied file record")
    db.refresh(new_file)

    logger.info("Drive file copied: id=%s -> new_id=%s", file_id, new_file.id)
    return DriveFileResponse.from_orm(new_file)


@router.get("/folders")
async def list_all_folders(
    request: Request,
    db: Session = Depends(get_db),
):
    """List all folders as a flat list for folder picker dialogs."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    folders = db.query(DriveFile).filter(DriveFile.is_dir == 1).order_by(DriveFile.filename.asc()).all()
    return {
        "items": [
            {"id": f.id, "filename": f.filename, "parent_id": f.parent_id, "oss_key": f.oss_key}
            for f in folders
        ]
    }


@router.get("/signed-url")
async def get_signed_download_url(
    request: Request,
    oss_key: str = Query(..., description="OSS object key"),
    expires_in: int = Query(3600, ge=60, le=86400),
):
    """Generate a signed URL for downloading a file directly from OSS."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not oss_key.startswith(DRIVE_PREFIX):
        raise HTTPException(status_code=400, detail=f"oss_key must start with '{DRIVE_PREFIX}'")

    if not (settings.OSS_ACCESS_KEY_ID and settings.OSS_ACCESS_KEY_SECRET):
        raise HTTPException(status_code=500, detail="OSS credentials not configured")

    url = _oss_signed_url("GET", oss_key, expires_in=expires_in)

    return {"url": url}


@router.post("/upload-url")
async def get_signed_upload_url(
    request: Request,
    oss_key: str = Query(..., description="Target OSS object key"),
    content_type: str = Query("application/octet-stream", description="File MIME type"),
):
    """Generate a signed PUT URL so the frontend can upload via XHR with progress."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not oss_key.startswith(DRIVE_PREFIX):
        raise HTTPException(status_code=400, detail=f"oss_key must start with '{DRIVE_PREFIX}'")

    if not (settings.OSS_ACCESS_KEY_ID and settings.OSS_ACCESS_KEY_SECRET):
        raise HTTPException(status_code=500, detail="OSS credentials not configured")

    url = _oss_signed_url("PUT", oss_key, expires_in=600, content_type=content_type)
    return {"url": url}


@router.get("/preview-text")
async def preview_text_file(
    request: Request,
    oss_key: str = Query(..., description="OSS object key"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(200, ge=50, le=1000, description="Lines per page"),
):
    """Preview a text file from OSS with line-based pagination."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not oss_key.startswith(DRIVE_PREFIX):
        raise HTTPException(status_code=400, detail=f"oss_key must start with '{DRIVE_PREFIX}'")

    if not (settings.OSS_ACCESS_KEY_ID and settings.OSS_ACCESS_KEY_SECRET):
        raise HTTPException(status_code=500, detail="OSS credentials not configured")

    # Download text content from OSS (limit to 2MB to avoid memory issues)
    MAX_PREVIEW_BYTES = 2 * 1024 * 1024
    try:
        content = _fetch_oss_object_range(oss_key, max_bytes=MAX_PREVIEW_BYTES)
    except Exception as e:
        logger.error("Failed to fetch text preview for %s: %s", oss_key, e)
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    # Decode as UTF-8
    try:
        text = content.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(status_code=400, detail="File is not a valid text file")

    lines = text.splitlines()
    total_lines = len(lines)
    total_pages = max(1, (total_lines + page_size - 1) // page_size)

    # Clamp page
    page = min(page, total_pages)
    start = (page - 1) * page_size
    end = min(start + page_size, total_lines)

    return {
        "content": "\n".join(lines[start:end]),
        "page": page,
        "page_size": page_size,
        "total_lines": total_lines,
        "total_pages": total_pages,
        "truncated": len(content) >= MAX_PREVIEW_BYTES,
    }


def _fetch_oss_object_range(oss_key: str, max_bytes: int) -> bytes:
    """Fetch a range of bytes from an OSS object using signed URL."""
    return _oss_request("GET", oss_key, expires_in=60, headers={"Range": f"bytes=0-{max_bytes - 1}"})


def _delete_oss_object(oss_key: str):
    """Delete an object from OSS using signed request."""
    if not (settings.OSS_ACCESS_KEY_ID and settings.OSS_ACCESS_KEY_SECRET):
        logger.warning("OSS credentials not configured, skipping OSS delete")
        return
    _oss_request("DELETE", oss_key, expires_in=60)
