import enum
from datetime import datetime
from sqlalchemy import String, Numeric, Enum, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, enum.Enum):
    UPI = "UPI"
    QR = "QR"
    CARD = "CARD"
    NETBANKING = "NETBANKING"
    STRIPE_CHECKOUT = "STRIPE_CHECKOUT"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    payment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    gateway: Mapped[str] = mapped_column(String(50), default="razorpay")  # 'razorpay' or 'stripe'
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), default=PaymentMethod.UPI, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True, nullable=False)
    signature: Mapped[str] = mapped_column(String(255), nullable=True)
    webhook_payload: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reservation = relationship("Reservation", back_populates="payment", uselist=False)
