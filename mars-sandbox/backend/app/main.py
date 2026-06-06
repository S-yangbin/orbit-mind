"""FastAPI application entry point."""
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .config import settings
from .database import init_db, SessionLocal, engine
from .auth import get_current_user
from .routers import auth, pages, tags, scan, nodes, commands, videos, meals, drive
from .scanner import scan_directories
from .ws.router import router as ws_router

logger = logging.getLogger(__name__)

# Frontend dist directory
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

# Background scheduler
_scheduler_thread = None


def _migrate_db():
    """Run database migrations for new columns."""
    from sqlalchemy import text, inspect
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('pages')]
    if 'category' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE pages ADD COLUMN category VARCHAR(32) NOT NULL DEFAULT 'work'"))
            conn.commit()
        logger.info("Migration: added 'category' column to pages table")

    # drive_files: add is_dir and parent_id columns (only if table exists)
    if 'drive_files' in inspector.get_table_names():
        drive_cols = [col['name'] for col in inspector.get_columns('drive_files')]
        if 'is_dir' not in drive_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE drive_files ADD COLUMN is_dir TINYINT NOT NULL DEFAULT 0"))
                conn.execute(text("ALTER TABLE drive_files ADD INDEX ix_drive_files_is_dir (is_dir)"))
                conn.commit()
            logger.info("Migration: added 'is_dir' column to drive_files table")
        if 'parent_id' not in drive_cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE drive_files ADD COLUMN parent_id INT NULL"))
                conn.execute(text("ALTER TABLE drive_files ADD INDEX ix_drive_files_parent_id (parent_id)"))
                conn.execute(text(
                    "ALTER TABLE drive_files ADD CONSTRAINT fk_drive_files_parent "
                    "FOREIGN KEY (parent_id) REFERENCES drive_files(id) ON DELETE CASCADE"
                ))
                conn.commit()
            logger.info("Migration: added 'parent_id' column to drive_files table")


def _start_background_scan():
    """Initial scan on startup, then periodic."""
    time.sleep(5)  # Wait for app to be ready
    scan_directories()

    interval = settings.SCAN_INTERVAL
    while True:
        time.sleep(interval)
        try:
            scan_directories()
        except Exception as e:
            logger.error("Background scan error: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    init_db()
    _migrate_db()
    logger.info("Database initialized.")

    # Ensure directories exist
    os.makedirs(settings.HTML_ROOT, exist_ok=True)
    os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)
    os.makedirs(settings.VIDEO_ROOT, exist_ok=True)
    os.makedirs(settings.VIDEO_AUDIO_DIR, exist_ok=True)
    os.makedirs(settings.VIDEO_NOTES_DIR, exist_ok=True)
    os.makedirs(settings.MEAL_PHOTO_DIR, exist_ok=True)

    # Start background scanner
    import threading
    t = threading.Thread(target=_start_background_scan, daemon=True)
    t.start()
    logger.info("Background scanner started (interval=%ds).", settings.SCAN_INTERVAL)

    yield

    # Shutdown
    logger.info("Shutting down.")


app = FastAPI(
    title="Mars Sandbox",
    description="Personal HTML page hosting service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(tags.router)
app.include_router(scan.router)
app.include_router(nodes.router)
app.include_router(commands.router)
app.include_router(videos.router)
app.include_router(meals.router)
app.include_router(drive.router)
app.include_router(ws_router)  # WebSocket路由


# --- Static file routes ---

# Thumbnails
thumb_dir = settings.THUMBNAIL_DIR
if os.path.isdir(thumb_dir):
    app.mount("/thumbnails", StaticFiles(directory=thumb_dir), name="thumbnails")

# Meal photos
meal_dir = settings.MEAL_PHOTO_DIR
if os.path.isdir(meal_dir):
    app.mount("/meal-photos", StaticFiles(directory=meal_dir), name="meal-photos")


# Frontend assets (JS/CSS bundles referenced by index.html at /assets/)
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


# HTML project files
@app.get("/files/{slug}/{path:path}")
async def serve_project_file(slug: str, path: str, request: Request):
    """Serve HTML project files (entry HTML + resources)."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Path traversal protection
    safe_slug = slug.replace("..", "").replace("/", "")
    safe_path = path.replace("..", "")
    file_path = os.path.join(settings.HTML_ROOT, safe_slug, safe_path)

    real_html_root = os.path.realpath(settings.HTML_ROOT)
    real_file_path = os.path.realpath(file_path)
    if not real_file_path.startswith(real_html_root):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Determine content type
    if path.endswith(".html") or path == "":
        media_type = "text/html; charset=utf-8"
    elif path.endswith(".css"):
        media_type = "text/css; charset=utf-8"
    elif path.endswith(".js"):
        media_type = "application/javascript; charset=utf-8"
    elif path.endswith(".png"):
        media_type = "image/png"
    elif path.endswith(".jpg") or path.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif path.endswith(".gif"):
        media_type = "image/gif"
    elif path.endswith(".svg"):
        media_type = "image/svg+xml"
    elif path.endswith(".json"):
        media_type = "application/json"
    else:
        media_type = "application/octet-stream"

    return FileResponse(file_path, media_type=media_type)


# --- Frontend static files ---

if FRONTEND_DIST.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


@app.get("/")
async def root():
    if FRONTEND_DIST.exists():
        return FileResponse(
            str(FRONTEND_DIST / "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )
    return JSONResponse({
        "app": "Mars Sandbox",
        "status": "running",
        "api_docs": "/docs",
        "note": "Frontend not built. Run `cd frontend && npm run build` to serve the UI.",
    })


@app.get("/health")
async def health():
    return {"status": "ok", "app": "mars-sandbox"}


# Catch-all for SPA routes — must be LAST to not shadow API/static routes
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    # Don't catch API routes — they should return proper 404s
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json") or full_path.startswith("redoc"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    if FRONTEND_DIST.exists():
        index_html = FRONTEND_DIST / "index.html"
        if index_html.exists():
            return FileResponse(str(index_html))
    return JSONResponse({"error": "Not found"}, status_code=404)
