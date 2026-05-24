"""Tag management routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Tag, PageTag
from ..schemas import TagCreate, TagUpdate, TagBase
from ..dependencies import current_user

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list)
def list_tags(db: Session = Depends(get_db), user=Depends(current_user)):
    """List all tags with page count."""
    tags = db.query(Tag).all()
    result = []
    for tag in tags:
        count = db.query(PageTag).filter(PageTag.tag_id == tag.id).count()
        result.append({"id": tag.id, "name": tag.name, "page_count": count})
    return result


@router.post("", response_model=dict)
def create_tag(body: TagCreate, db: Session = Depends(get_db), user=Depends(current_user)):
    """Create a new tag."""
    existing = db.query(Tag).filter(Tag.name == body.name).first()
    if existing:
        return {"error": "Tag already exists"}
    tag = Tag(name=body.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return {"id": tag.id, "name": tag.name}


@router.put("/{tag_id}", response_model=dict)
def update_tag(
    tag_id: int, body: TagUpdate, db: Session = Depends(get_db), user=Depends(current_user)
):
    """Rename a tag."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        return {"error": "Tag not found"}

    # Check for duplicate name
    existing = db.query(Tag).filter(Tag.name == body.name, Tag.id != tag_id).first()
    if existing:
        return {"error": "Tag name already exists"}

    tag.name = body.name
    db.commit()
    return {"id": tag.id, "name": tag.name}


@router.delete("/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    """Delete a tag (removes associations)."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        return {"error": "Tag not found"}
    db.delete(tag)
    db.commit()
    return {"success": True, "message": "Tag deleted"}
