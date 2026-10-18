from datetime import datetime
from typing import List
from sqlalchemy import String, Text, Numeric, Boolean, Integer, DateTime, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan", order_by="MenuItem.name")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Comma-separated or array tags: 'top-recipe', 'chef-special', 'vegetarian', 'spicy'
    tags: Mapped[str] = mapped_column(String(255), default="")
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_top_recipe: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_chef_special: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="items")
