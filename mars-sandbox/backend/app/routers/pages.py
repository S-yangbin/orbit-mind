"""Pages CRUD routes."""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Page, Tag, PageTag
from ..schemas import PageInDB, PageUpdate, TagBase
from ..dependencies import current_user

router = APIRouter(prefix="/api/pages", tags=["pages"])


@router.get("", response_model=dict)
def list_pages(
    q: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    sort: Optional[str] = Query("updated_at"),
    order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    """List pages with search, filter, sort, and pagination."""
    query = db.query(Page)

    # Search by title/description
    if q:
        q_pattern = f"%{q}%"
        query = query.filter(
            (Page.custom_title.like(q_pattern))
            | (Page.scanned_title.like(q_pattern))
            | (Page.title.like(q_pattern))
            | (Page.description.like(q_pattern))
        )

    # Filter by tag
    if tag:
        query = query.join(Page.tags).join(PageTag.tag).filter(Tag.name == tag)

    # Sort
    sort_field = getattr(Page, sort, Page.updated_at)
    if order.lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())

    # Paginate
    total = query.count()
    pages = query.offset((page - 1) * page_size).limit(page_size).all()

    # Build response
    items = []
    for p in pages:
        items.append({
            "id": p.id,
            "slug": p.slug,
            "title": p.display_title,
            "description": p.display_description,
            "thumbnail": p.thumbnail,
            "entry_file": p.entry_file,
            "is_customized": p.is_customized,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "synced_at": p.synced_at,
            "tags": [{"id": pt.tag.id, "name": pt.tag.name} for pt in p.tags],
        })

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/{page_id}", response_model=dict)
def get_page(page_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    """Get page detail."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        return {"error": "Page not found"}
    return {
        "id": page.id,
        "slug": page.slug,
        "title": page.display_title,
        "description": page.display_description,
        "thumbnail": page.thumbnail,
        "entry_file": page.entry_file,
        "is_customized": page.is_customized,
        "created_at": page.created_at,
        "updated_at": page.updated_at,
        "synced_at": page.synced_at,
        "tags": [{"id": pt.tag.id, "name": pt.tag.name} for pt in page.tags],
    }


@router.put("/{page_id}", response_model=dict)
def update_page(
    page_id: int,
    body: PageUpdate,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    """Update page metadata (user edits are protected from scan override)."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        return {"error": "Page not found"}

    if body.title is not None:
        page.custom_title = body.title
        page.is_customized = 1

    if body.description is not None:
        page.custom_description = body.description
        page.is_customized = 1

    # Update tags
    if body.tags is not None:
        # Remove existing tags
        db.query(PageTag).filter(PageTag.page_id == page.id).delete()
        for tag_name in body.tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            db.add(PageTag(page_id=page.id, tag_id=tag.id))

    db.commit()
    db.refresh(page)

    return {
        "id": page.id,
        "slug": page.slug,
        "title": page.display_title,
        "description": page.display_description,
        "thumbnail": page.thumbnail,
        "entry_file": page.entry_file,
        "is_customized": page.is_customized,
        "tags": [{"id": pt.tag.id, "name": pt.tag.name} for pt in page.tags],
    }


@router.delete("/{page_id}")
def delete_page(page_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    """Delete page record (does not delete files)."""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        return {"error": "Page not found"}
    db.delete(page)
    db.commit()
    return {"success": True, "message": "Page deleted"}
