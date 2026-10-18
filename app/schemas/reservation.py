from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.reservation import ReservationStatus


class TableBase(BaseModel):
    table_number: str
    capacity: int = Field(..., gt=0)
    location: Optional[str] = "indoor"
    is_active: Optional[bool] = True


class TableCreate(TableBase):
    pass


class TableResponse(TableBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SlotAvailabilityQuery(BaseModel):
    date: date
    guests: int = Field(..., gt=0)


class AvailableSlot(BaseModel):
    slot_start: str
    slot_end: str
    table_id: int
    table_number: str
    capacity: int
    location: str
    is_available: bool


class ReservationHoldRequest(BaseModel):
    table_id: int
    date: date
    slot_start: str
    session_id: str


class ReservationHoldResponse(BaseModel):
    success: bool
    session_id: str
    held_until_seconds: int
    message: str


class ReservationCreate(BaseModel):
    table_id: int
    reservation_date: date
    slot_start: str
    slot_end: str
    guests: int = Field(..., gt=0)
    customer_name: str
    customer_email: str
    customer_phone: str
    special_requests: Optional[str] = None
    session_id: str  # must match active hold in Redis


class ReservationResponse(BaseModel):
    id: int
    table_id: int
    user_id: Optional[int] = None
    payment_id: Optional[int] = None
    customer_name: str
    customer_email: str
    customer_phone: str
    reservation_date: date
    slot_start: str
    slot_end: str
    guests: int
    special_requests: Optional[str] = None
    status: ReservationStatus
    created_at: datetime
    table: Optional[TableResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ReservationStatusUpdate(BaseModel):
    status: ReservationStatus


class ReservationRescheduleRequest(BaseModel):
    reservation_date: date
    slot_start: str
    slot_end: str
    table_id: Optional[int] = None

