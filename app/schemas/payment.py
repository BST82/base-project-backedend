from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.payment import PaymentMethod, PaymentStatus


class PaymentOrderCreate(BaseModel):
    reservation_id: int
    gateway: Optional[str] = "razorpay"
    method: Optional[PaymentMethod] = PaymentMethod.UPI


class PaymentOrderResponse(BaseModel):
    order_id: str
    amount: float
    currency: str
    gateway: str
    key_id: Optional[str] = None
    client_secret: Optional[str] = None  # for Stripe Elements
    qr_code_string: Optional[str] = None  # for simulated / dynamic UPI QR
    reservation_id: int


class PaymentVerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: Optional[str] = None
    gateway: Optional[str] = "razorpay"


class PaymentResponse(BaseModel):
    id: int
    order_id: str
    payment_id: Optional[str] = None
    gateway: str
    method: PaymentMethod
    amount: float
    currency: str
    status: PaymentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
