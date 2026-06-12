"""HTML directory scanner: extracts metadata and generates thumbnails."""
import os
import hashlib
import logging
import re
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from threading import Lock
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from .config import settings
from .models import Page, Tag, PageTag
from .database import SessionLocal
from .utils.timezone import beijing_now

logger = logging.getLogger(__name__)

# Lock to prevent concurrent scans
_scan_lock = Lock()
_last_scan_at: Optional[datetime] = None
_last_result: Optional[str] = None


def is_scanning() -> bool:
    return _scan_lock.locked()


def get_last_scan_info() -> dict:
    return {
        "last_scan_at": _last_scan_at,
        "last_result": _last_result,
    }


def compute_dir_hash(dir_path: str) -> str:
    """Compute a combined hash for all files in a directory based on mtime + size."""
    hasher = hashlib.md5()
    for root, dirs, files in os.walk(dir_path):
        dirs.sort()
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            try:
                st = os.stat(fpath)
                hasher.update(f"{fname}:{st.st_mtime}:{st.st_size}".encode())
            except OSError:
                pass
    return hasher.hexdigest()


def extract_metadata(html_path: str) -> dict:
    """Extract title, description, keywords from an HTML file."""
    result = {"title": None, "description": None, "keywords": []}
    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        soup = BeautifulSoup(content, "html.parser")

        # Title
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            result["title"] = title_tag.get_text(strip=True)
        else:
            h1 = soup.find("h1")
            if h1 and h1.get_text(strip=True):
                result["title"] = h1.get_text(strip=True)

        # Description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content", "").strip():
            result["description"] = meta_desc["content"].strip()[:500]
        else:
            # Fallback: first <p> tag text
            p_tag = soup.find("p")
            if p_tag and p_tag.get_text(strip=True):
                result["description"] = p_tag.get_text(strip=True)[:200]

        # Keywords / Tags
        meta_kw = soup.find("meta", attrs={"name": "keywords"})
        if meta_kw and meta_kw.get("content", "").strip():
            result["keywords"] = [
                k.strip() for k in meta_kw["content"].split(",") if k.strip()
            ]

    except Exception as e:
        logger.error("Error extracting metadata from %s: %s", html_path, e)

    return result


def generate_thumbnail(slug: str, html_path: str) -> Optional[str]:
    """Generate thumbnail screenshot using Playwright."""
    thumb_path = os.path.join(settings.THUMBNAIL_DIR, f"{slug}.png")
    os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            file_url = f"file://{os.path.abspath(html_path)}"
            page.goto(file_url, wait_until="domcontentloaded", timeout=10000)
            page.screenshot(path=thumb_path, full_page=False)
            browser.close()

        # Resize if too large (keep max width 400)
        try:
            from PIL import Image
            img = Image.open(thumb_path)
            if img.width > 400:
                ratio = 400 / img.width
                new_size = (400, int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                img.save(thumb_path)
        except ImportError:
            pass  # PIL not installed, keep original

        return f"/thumbnails/{slug}.png"
    except Exception as e:
        logger.error("Thumbnail generation failed for %s: %s", slug, e)
        return None


def _find_entry_file(dir_path: str) -> Optional[str]:
    """Find the entry HTML file in a project directory."""
    index_path = os.path.join(dir_path, "index.html")
    if os.path.isfile(index_path):
        return "index.html"

    # Find first .html file
    for f in sorted(os.listdir(dir_path)):
        if f.endswith(".html") and os.path.isfile(os.path.join(dir_path, f)):
            return f
    return None


def scan_directories() -> dict:
    """Main scan logic: sync HTML directories with database."""
    global _last_scan_at, _last_result

    if _scan_lock.locked():
        return {"status": "already_running"}

    with _scan_lock:
        _last_scan_at = beijing_now()
        results = {"new": 0, "updated": 0, "unchanged": 0, "removed": 0, "errors": 0}

        try:
            db = SessionLocal()
            html_root = Path(settings.HTML_ROOT)

            if not html_root.exists():
                results["errors"] += 1
                _last_result = f"HTML_ROOT not found: {html_root}"
                return results

            # Get all existing slugs from filesystem
            existing_slugs = set()
            for item in sorted(html_root.iterdir()):
                if item.is_dir():
                    slug = item.name
                    existing_slugs.add(slug)
                    try:
                        _sync_page(db, item, slug, results)
                    except Exception as e:
                        logger.error("Error syncing %s: %s", slug, e)
                        results["errors"] += 1

            # Remove pages whose directories no longer exist
            all_pages = db.query(Page).all()
            for page in all_pages:
                if page.slug not in existing_slugs:
                    # Remove associated tags
                    db.query(PageTag).filter(PageTag.page_id == page.id).delete()
                    db.delete(page)
                    results["removed"] += 1

            db.commit()

        except Exception as e:
            _last_result = f"Scan failed: {str(e)}"
            results["errors"] += 1
        finally:
            db.close()
            _last_result = (
                f"Scan complete: {results['new']} new, "
                f"{results['updated']} updated, "
                f"{results['unchanged']} unchanged, "
                f"{results['removed']} removed, "
                f"{results['errors']} errors"
            )

        return results


def _sync_page(db: Session, dir_path: Path, slug: str, results: dict):
    """Sync a single project directory."""
    entry_file = _find_entry_file(str(dir_path))
    if not entry_file:
        results["errors"] += 1
        return

    entry_path = str(dir_path / entry_file)
    dir_hash = compute_dir_hash(str(dir_path))

    existing = db.query(Page).filter(Page.slug == slug).first()

    if existing:
        # Check if content changed
        if existing.content_hash == dir_hash:
            results["unchanged"] += 1
            existing.synced_at = beijing_now()
            return

        # Content changed
        existing.content_hash = dir_hash
        existing.synced_at = beijing_now()
        existing.entry_file = entry_file

        # Only update scanned fields if not customized
        if not existing.is_customized:
            meta = extract_metadata(entry_path)
            existing.scanned_title = meta["title"] or slug
            existing.scanned_description = meta["description"]
            existing.title = meta["title"] or slug
            existing.description = meta["description"]

            # Update tags from keywords
            if meta["keywords"]:
                _sync_tags(db, existing, meta["keywords"])

        # Regenerate thumbnail
        thumb = generate_thumbnail(slug, entry_path)
        if thumb:
            existing.thumbnail = thumb

        results["updated"] += 1
    else:
        # New project
        meta = extract_metadata(entry_path)
        thumb = generate_thumbnail(slug, entry_path)

        page = Page(
            slug=slug,
            title=meta["title"] or slug,
            description=meta["description"],
            scanned_title=meta["title"] or slug,
            scanned_description=meta["description"],
            thumbnail=thumb,
            entry_file=entry_file,
            content_hash=dir_hash,
            synced_at=beijing_now(),
            category="work",
        )
        db.add(page)
        db.flush()  # Get page.id

        if meta["keywords"]:
            _sync_tags(db, page, meta["keywords"])

        results["new"] += 1


def _sync_tags(db: Session, page: Page, keywords: list):
    """Sync tags for a page."""
    # Remove existing tags
    db.query(PageTag).filter(PageTag.page_id == page.id).delete()

    for kw in keywords:
        tag = db.query(Tag).filter(Tag.name == kw).first()
        if not tag:
            tag = Tag(name=kw)
            db.add(tag)
            db.flush()
        db.add(PageTag(page_id=page.id, tag_id=tag.id))
