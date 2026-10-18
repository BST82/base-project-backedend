from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class StoryBase(BaseModel):
    title: str
    slug: Optional[str] = None
    excerpt: str
    content: str
    cover_image: Optional[str] = None
    author: Optional[str] = "Culinary Team"
    author_name: Optional[str] = None
    category: str = "Harvest Stories"
    read_time: Optional[str] = "4 min read"
    reading_time_minutes: Optional[int] = None
    tags: Optional[str] = None
    is_published: bool = True


class StoryCreate(StoryBase):
    pass


class StoryUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    author: Optional[str] = None
    author_name: Optional[str] = None
    category: Optional[str] = None
    read_time: Optional[str] = None
    reading_time_minutes: Optional[int] = None
    tags: Optional[str] = None
    is_published: Optional[bool] = None


class StoryResponse(StoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
