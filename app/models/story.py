from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Rich text / HTML
    cover_image: Mapped[str] = mapped_column(String(500), nullable=True)
    author: Mapped[str] = mapped_column(String(100), default="Culinary Team")
    category: Mapped[str] = mapped_column(String(50), default="Harvest Stories", index=True)
    read_time: Mapped[str] = mapped_column(String(30), default="4 min read")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def author_name(self) -> str:
        return self.author or "Culinary Team"

    @property
    def reading_time_minutes(self) -> int:
        if self.read_time:
            parts = [int(s) for s in self.read_time.split() if s.isdigit()]
            if parts:
                return parts[0]
        return 4

    @property
    def tags(self) -> str:
        return "Organic, Farm-to-Table"

