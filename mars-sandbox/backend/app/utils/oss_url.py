"""Generate signed OSS URLs for direct browser access to video files."""
import hmac
import hashlib
import base64
import urllib.parse
import time

from ..config import settings


def generate_signed_video_url(file_path: str, expires_in: int = 86400) -> str:
    """Generate a time-limited signed URL for a video file in OSS.

    Args:
        file_path: Relative path within the videos/ prefix (e.g., "abc123.mp4").
        expires_in: URL validity in seconds (default 24h).

    Returns:
        Full signed OSS URL that the browser can use directly.
    """
    if not (settings.OSS_ACCESS_KEY_ID and settings.OSS_ACCESS_KEY_SECRET):
        # Fallback: return API stream URL
        return ""

    expires = int(time.time()) + expires_in
    object_name = f"videos/{file_path}"

    # Build the canonical string to sign
    string_to_sign = f"GET\n\n\n{expires}\n/{settings.OSS_BUCKET}/{object_name}"

    # HMAC-SHA1 signature
    signature_bytes = hmac.new(
        settings.OSS_ACCESS_KEY_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    signature = base64.b64encode(signature_bytes).decode("utf-8")
    signature_encoded = urllib.parse.quote(signature, safe="")

    return (
        f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT}"
        f"/{object_name}"
        f"?OSSAccessKeyId={settings.OSS_ACCESS_KEY_ID}"
        f"&Expires={expires}"
        f"&Signature={signature_encoded}"
    )