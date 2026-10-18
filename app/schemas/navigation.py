from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class NavItemBase(BaseModel):
    label: str
    route: str
    display_order: int = 0
    is_active: bool = True
    is_external: bool = False


class NavItemCreate(NavItemBase):
    create_page: bool = False
    page_title: Optional[str] = None
    page_subtitle: Optional[str] = None
    page_hero_image: Optional[str] = None


class NavItemUpdate(BaseModel):
    label: Optional[str] = None
    route: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_external: Optional[bool] = None


class NavItemResponse(NavItemBase):
    id: int
    created_at: datetime
    has_dynamic_page: Optional[bool] = False
    page_slug: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
