from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    customer_name: str
    rating: int = Field(..., ge=1, le=5)
    comment: str


class ReviewCreate(ReviewBase):
    pass


class ReviewModerationUpdate(BaseModel):
    is_approved: bool


class ReviewResponse(ReviewBase):
    id: int
    user_id: Optional[int] = None
    is_approved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
