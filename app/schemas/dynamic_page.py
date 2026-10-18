from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict


class HeroSlideConfig(BaseModel):
    image_url: str
    badge_text: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    caption: Optional[str] = None
    button_primary_text: Optional[str] = None
    button_primary_link: Optional[str] = None


class ContentBlockItem(BaseModel):
    id: Optional[str] = None
    block_type: str = "rich_text"  # 'rich_text' | 'split_content' | 'feature_grid' | 'cta_banner'
    badge: Optional[str] = None
    heading: str
    subheading: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None
    button_text: Optional[str] = None
    button_link: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None


class DynamicPageBase(BaseModel):
    slug: str
    title: str
    subtitle: Optional[str] = None
    meta_description: Optional[str] = None
    hero_slides: Optional[List[Dict[str, Any]]] = None
    content_blocks: Optional[List[Dict[str, Any]]] = None
    is_published: bool = True


class DynamicPageCreate(DynamicPageBase):
    nav_item_id: Optional[int] = None


class DynamicPageUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    slug: Optional[str] = None
    meta_description: Optional[str] = None
    hero_slides: Optional[List[Dict[str, Any]]] = None
    content_blocks: Optional[List[Dict[str, Any]]] = None
    is_published: Optional[bool] = None


class DynamicPageResponse(DynamicPageBase):
    id: int
    nav_item_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
