from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DynamicPage(Base):
    __tablename__ = "dynamic_pages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nav_item_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("nav_items.id", ondelete="CASCADE"), nullable=True, unique=True
    )
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    
    # Hero slider configuration (multi-image upload, captions, headlines)
    hero_slides: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)

    # Modular inner content blocks (rich text, split layouts, features, CTA)
    content_blocks: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)

    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to NavItem
    nav_item = relationship("NavItem", back_populates="dynamic_page")
