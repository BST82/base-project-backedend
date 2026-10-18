from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

import re

db_url = settings.DATABASE_URL.strip()
# Clean accidental brackets around password (e.g., :[password]@ -> :password@)
db_url = re.sub(r":\[([^\]]+)\]@", r":\1@", db_url)

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg_async://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg_async://", 1)

# Ensure SSL is enforced for cloud-hosted Supabase instances
if "supabase.co" in db_url and "sslmode=" not in db_url:
    separator = "&" if "?" in db_url else "?"
    db_url = f"{db_url}{separator}sslmode=require"

if "sqlite" in db_url:
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
    )
else:
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
