import re
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_admin
from app.models.story import Story
from app.schemas.story import StoryCreate, StoryUpdate, StoryResponse

router = APIRouter(prefix="/stories", tags=["Our Stories Blog Engine CMS"])


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text)


@router.get("", response_model=List[StoryResponse])
async def list_published_stories(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Public endpoint: returns all published stories ordered by creation date."""
    query = select(Story).where(Story.is_published == True)
    if category and category.lower() != "all":
        query = query.where(Story.category.ilike(category))
    
    result = await db.execute(query.order_by(Story.created_at.desc()))
    return result.scalars().all()


@router.get("/admin/all", response_model=List[StoryResponse])
async def list_all_stories_admin(
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    """Admin endpoint: returns all stories including drafts."""
    result = await db.execute(select(Story).order_by(Story.created_at.desc()))
    return result.scalars().all()


@router.get("/{slug_or_id}", response_model=StoryResponse)
async def get_single_story(slug_or_id: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint: read a full story by slug or numeric ID."""
    if slug_or_id.isdigit():
        result = await db.execute(select(Story).where(Story.id == int(slug_or_id)))
    else:
        result = await db.execute(select(Story).where(Story.slug == slug_or_id))
    
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    story_in: StoryCreate,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    data = story_in.model_dump()
    slug = data.get("slug") or slugify(data.get("title", "story"))
    existing = await db.execute(select(Story).where(Story.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    
    data["slug"] = slug
    if data.get("author_name"):
        data["author"] = data.get("author_name")
    if data.get("reading_time_minutes"):
        data["read_time"] = f"{data.get('reading_time_minutes')} min read"

    valid_cols = {"title", "slug", "excerpt", "content", "cover_image", "author", "category", "read_time", "is_published"}
    clean_data = {k: v for k, v in data.items() if k in valid_cols}
    story = Story(**clean_data)
    db.add(story)
    await db.commit()
    await db.refresh(story)
    return story


@router.put("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: int,
    story_in: StoryUpdate,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    data = story_in.model_dump(exclude_unset=True)
    if data.get("author_name"):
        data["author"] = data.get("author_name")
    if data.get("reading_time_minutes"):
        data["read_time"] = f"{data.get('reading_time_minutes')} min read"

    valid_cols = {"title", "slug", "excerpt", "content", "cover_image", "author", "category", "read_time", "is_published"}
    for field, val in data.items():
        if field in valid_cols:
            setattr(story, field, val)

    await db.commit()
    await db.refresh(story)
    return story


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_active_admin)
):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    await db.delete(story)
    await db.commit()
