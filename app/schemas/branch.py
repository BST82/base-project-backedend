from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BranchBase(BaseModel):
    name: str
    city: str
    address: str
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    latitude: float
    longitude: float
    opening_hours: Optional[str] = None
    operating_hours: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    opening_hours: Optional[str] = None
    operating_hours: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
