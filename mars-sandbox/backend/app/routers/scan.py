"""Scan trigger and status routes."""
import threading
from fastapi import APIRouter, Depends
from ..dependencies import current_user, require_auth_or_api_key
from ..scanner import scan_directories, is_scanning, get_last_scan_info

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("", response_model=dict)
def trigger_scan(user=Depends(require_auth_or_api_key)):
    """Manually trigger a directory scan."""
    if is_scanning():
        return {"status": "already_running", "message": "A scan is already in progress"}

    # Run scan in background thread
    def run():
        scan_directories()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return {"status": "started", "message": "Scan started in background"}


@router.get("/status", response_model=dict)
def scan_status(user=Depends(require_auth_or_api_key)):
    """Get current scan status."""
    info = get_last_scan_info()
    return {
        "is_running": is_scanning(),
        "last_scan_at": info["last_scan_at"],
        "last_result": info["last_result"],
    }
