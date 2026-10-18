from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BannerSlideBase(BaseModel):
    badge_text: str = "EST. 2026 • SCRATCH KITCHEN"
    script_text: str = "Honest to"
    title: str
    subtitle: Optional[str] = None
    ribbon_text: str = "ARTISAN GASTRONOMY"
    image_url: str
    button_primary_text: str = "Make a Reservation"
    button_primary_link: str = "/reserve"
    button_secondary_text: str = "Explore Menu & Recipes"
    button_secondary_link: str = "/menu"
    display_order: int = 0
    is_active: bool = True


class BannerSlideCreate(BannerSlideBase):
    pass


class BannerSlideUpdate(BaseModel):
    badge_text: Optional[str] = None
    script_text: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    ribbon_text: Optional[str] = None
    image_url: Optional[str] = None
    button_primary_text: Optional[str] = None
    button_primary_link: Optional[str] = None
    button_secondary_text: Optional[str] = None
    button_secondary_link: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class BannerSlideResponse(BannerSlideBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
