from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BannerSlide(Base):
    __tablename__ = "banner_slides"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    badge_text: Mapped[str] = mapped_column(String(100), default="EST. 2026 • SCRATCH KITCHEN")
    script_text: Mapped[str] = mapped_column(String(100), default="Honest to")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str] = mapped_column(Text, nullable=True)
    ribbon_text: Mapped[str] = mapped_column(String(100), default="ARTISAN GASTRONOMY")
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    button_primary_text: Mapped[str] = mapped_column(String(50), default="Make a Reservation")
    button_primary_link: Mapped[str] = mapped_column(String(100), default="/reserve")
    button_secondary_text: Mapped[str] = mapped_column(String(50), default="Explore Menu & Recipes")
    button_secondary_link: Mapped[str] = mapped_column(String(100), default="/menu")
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
