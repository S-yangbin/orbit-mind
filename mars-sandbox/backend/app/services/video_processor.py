"""Video processing service: ffmpeg audio extraction, ASR via bailian-cli, LLM segment analysis."""
import json
import logging
import os
import re
import subprocess
import threading
from pathlib import Path
from typing import Optional

from ..config import settings
from ..database import SessionLocal
from ..models import Video, VideoSegment, SegmentProgress

logger = logging.getLogger(__name__)

SEGMENT_TYPES = ["intro", "qa", "explanation", "outro", "other"]


def _bl_base_cmd() -> list:
    """Build base bl command list with optional API key."""
    cmd = [settings.BL_PATH]
    if settings.DASHSCOPE_API_KEY:
        cmd += ["--api-key", settings.DASHSCOPE_API_KEY]
    return cmd


def extract_audio(video_id: int, video_path: str) -> str:
    """Extract audio track from video file using ffmpeg.

    Returns path to the extracted .wav file.
    """
    os.makedirs(settings.VIDEO_AUDIO_DIR, exist_ok=True)
    audio_path = os.path.join(settings.VIDEO_AUDIO_DIR, f"{video_id}.wav")

    cmd = [
        settings.FFMPEG_PATH, "-y",
        "-i", video_path,
        "-vn",              # no video
        "-acodec", "pcm_s16le",
        "-ar", "16000",     # 16kHz for ASR
        "-ac", "1",         # mono
        audio_path,
    ]
    logger.info("Extracting audio (ffmpeg=%s): %s", settings.FFMPEG_PATH, " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr}")

    return audio_path


def transcribe(audio_path: str) -> dict:
    """Run bailian-cli ASR on the audio file.

    Returns parsed transcription JSON with timestamps.
    """
    # bl speech recognize auto-uploads local files
    out_json_path = audio_path.replace(".wav", "_transcription.json")
    cmd = _bl_base_cmd() + [
        "speech", "recognize",
        "--url", audio_path,
        "--language", "en",
        "--diarization",
        "--out", out_json_path,
        "--non-interactive",
    ]
    logger.info("Running ASR: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        raise RuntimeError(f"ASR failed: {result.stderr}")

    # Read the output JSON
    if os.path.exists(out_json_path):
        with open(out_json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Try parsing stdout
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning("Could not parse ASR output as JSON, using raw text")
        return {"raw": result.stdout}


def _format_transcription_for_llm(transcription: dict) -> str:
    """Convert transcription JSON to a readable text format for the LLM."""
    # Try to extract sentences/segments with timestamps
    # FunASR format typically has 'transcription' key with list of segments
    if isinstance(transcription, dict):
        # Common FunASR response format
        segments = transcription.get("transcription", [])
        if not segments:
            # Try alternative keys
            segments = transcription.get("results", []) or transcription.get("sentences", [])

        if segments:
            lines = []
            for i, seg in enumerate(segments):
                if isinstance(seg, dict):
                    text = seg.get("text", "") or seg.get("sentence", "")
                    start = seg.get("start", 0) or seg.get("begin_time", 0)
                    end = seg.get("end", 0) or seg.get("end_time", 0)
                    speaker = seg.get("speaker", "")
                    # Convert ms to seconds if needed
                    if start > 1000:
                        start = int(start) / 1000
                        end = int(end) / 1000
                    speaker_tag = f"[{speaker}] " if speaker else ""
                    lines.append(f"[{_format_time(int(start))} - {_format_time(int(end))}] {speaker_tag}{text}")
                elif isinstance(seg, str):
                    lines.append(seg)
            return "\n".join(lines)

    # Fallback: return raw JSON string
    return json.dumps(transcription, ensure_ascii=False, indent=2)


def _format_time(seconds: int) -> str:
    """Format seconds to mm:ss."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def analyze_segments(transcription: dict) -> list[dict]:
    """Use LLM to analyze transcription and identify video segments.

    Returns list of segment dicts with: title, segment_type, start_time, end_time, transcription.
    """
    formatted = _format_transcription_for_llm(transcription)
    if len(formatted) > 30000:
        formatted = formatted[:30000] + "\n... (truncated)"

    system_prompt = """You are an expert at analyzing English teaching video transcriptions.
Your task is to identify distinct logical segments in the video content.

The transcription includes timestamps in [MM:SS - MM:SS] format. Each line is one spoken sentence.

Output a JSON array of segments. Each segment must have:
- "title": A short descriptive title in English (e.g., "Self-introduction", "Vocabulary: Colors", "Q&A: Daily Routine")
- "segment_type": One of "intro", "qa", "explanation", "outro", "other"
- "start_time": Start time in seconds (integer)
- "end_time": End time in seconds (integer)
- "transcription": The full transcription text for this segment

Rules:
1. intro = teacher greeting, self-introduction, lesson overview
2. qa = question and answer exchange between teacher and student
3. explanation = teacher explaining concepts, vocabulary, grammar, pronunciation
4. outro = closing remarks, homework assignment
5. other = anything that doesn't fit above
6. Segments should be contiguous and cover the entire video timeline
7. Each segment should be a meaningful logical unit (typically 30s-3min)
8. Keep original timestamps and text exactly as in the transcription

Output ONLY the JSON array, no other text."""

    cmd = _bl_base_cmd() + [
        "text", "chat",
        "--system", system_prompt,
        "--message", formatted,
        "--output", "json",
        "--non-interactive",
    ]
    logger.info("Running LLM segment analysis...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        raise RuntimeError(f"LLM analysis failed: {result.stderr}")

    # Parse LLM output - try to extract JSON array
    output = result.stdout.strip()

    # Try parsing as JSON directly
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict) and "choices" in parsed:
            # OpenAI-compatible format
            content = parsed["choices"][0]["message"]["content"]
            return _extract_json_array(content)
        elif isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and "content" in parsed:
            return _extract_json_array(parsed["content"])
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array from text
    return _extract_json_array(output)


def _extract_json_array(text: str) -> list[dict]:
    """Extract a JSON array from text that may contain markdown fences or extra content."""
    # Remove markdown code fences
    text = re.sub(r'```(?:json)?\s*', '', text)

    # Find the first [ and last ]
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    logger.error("Could not extract JSON array from LLM output: %s", text[:500])
    raise ValueError("Failed to parse LLM segment analysis output")


def process_video(video_id: int):
    """Full processing pipeline for a video: audio extract -> ASR -> LLM segments.

    Runs in a background thread. Updates video status in DB.
    """
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error("Video %s not found", video_id)
            return

        # Build full path
        oss_root = settings.VIDEO_ROOT
        video_path = os.path.join(oss_root, os.path.basename(video.file_path))
        if not os.path.exists(video_path):
            # Try relative path directly
            video_path = video.file_path
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

        video.status = "processing"
        db.commit()

        # Step 0: Clear old segments on retry (direct delete for safety)
        old_count = db.query(VideoSegment).filter(VideoSegment.video_id == video_id).count()
        if old_count > 0:
            db.query(VideoSegment).filter(VideoSegment.video_id == video_id).delete()
            db.flush()
            logger.info("Video %s: cleared %d old segments for retry", video_id, old_count)

        # Step 1: Extract audio
        logger.info("Video %s: extracting audio...", video_id)
        audio_path = extract_audio(video_id, video_path)
        logger.info("Video %s: audio extracted to %s", video_id, audio_path)

        # Step 2: ASR
        logger.info("Video %s: running ASR...", video_id)
        transcription = transcribe(audio_path)
        video.transcription_json = json.dumps(transcription, ensure_ascii=False)
        db.commit()
        logger.info("Video %s: ASR complete", video_id)

        # Step 3: LLM segment analysis
        logger.info("Video %s: analyzing segments with LLM...", video_id)
        segments = analyze_segments(transcription)
        logger.info("Video %s: got %d segments", video_id, len(segments))

        # Step 4: Create segment records
        for i, seg_data in enumerate(segments):
            segment = VideoSegment(
                video_id=video_id,
                title=seg_data.get("title", f"Segment {i + 1}"),
                segment_type=seg_data.get("segment_type", "other"),
                start_time=int(seg_data.get("start_time", 0)),
                end_time=int(seg_data.get("end_time", 0)),
                transcription=seg_data.get("transcription", ""),
                sort_order=i,
            )
            db.add(segment)
            db.flush()  # Get segment ID

            # Create progress record
            progress = SegmentProgress(segment_id=segment.id)
            db.add(progress)

        video.status = "ready"
        db.commit()
        logger.info("Video %s: processing complete", video_id)

    except Exception as e:
        logger.exception("Video %s processing failed", video_id)
        try:
            video.status = "error"
            video.error_message = str(e)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def start_async_processing(video_id: int):
    """Start video processing in a background thread."""
    thread = threading.Thread(target=process_video, args=(video_id,), daemon=True)
    thread.start()
    return thread