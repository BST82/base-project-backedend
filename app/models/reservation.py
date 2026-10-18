import enum
from datetime import datetime, date, time
from sqlalchemy import String, Integer, Date, Time, Enum, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ReservationStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Table(Base):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    table_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(50), default="indoor")  # indoor, outdoor, patio, window
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    reservations = relationship("Reservation", back_populates="table", cascade="all, delete-orphan")


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, unique=True)

    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    
    reservation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    slot_start: Mapped[str] = mapped_column(String(10), nullable=False)  # "18:00"
    slot_end: Mapped[str] = mapped_column(String(10), nullable=False)    # "19:30"
    guests: Mapped[int] = mapped_column(Integer, nullable=False)
    special_requests: Mapped[str] = mapped_column(String(255), nullable=True)

    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus),
        default=ReservationStatus.PENDING_PAYMENT,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reservations")
    table = relationship("Table", back_populates="reservations")
    payment = relationship("Payment", back_populates="reservation")

    # Composite index for collision queries
    __table_args__ = (
        Index("idx_table_date_slot", "table_id", "reservation_date", "slot_start", "status"),
    )
