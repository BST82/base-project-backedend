from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

import re

db_url = settings.DATABASE_URL.strip()
# Clean accidental brackets around password (e.g., :[password]@ -> :password@)
db_url = re.sub(r":\[([^\]]+)\]@", r":\1@", db_url)

# Normalize PostgreSQL scheme to SQLAlchemy 2.0 async dialect
if db_url.startswith("postgres://"):
    db_url = "postgresql+psycopg://" + db_url[len("postgres://"):]
elif db_url.startswith("postgresql://"):
    db_url = "postgresql+psycopg://" + db_url[len("postgresql://"):]
elif db_url.startswith("postgresql+psycopg_async://"):
    db_url = "postgresql+psycopg://" + db_url[len("postgresql+psycopg_async://"):]

# Ensure SSL is enforced for cloud-hosted database providers (Supabase, Render, Neon)
is_cloud_db = any(host in db_url for host in ("supabase.co", "render.com", "neon.tech", "pooler.supabase.com"))
if is_cloud_db:
    if "asyncpg" in db_url:
        if "ssl=" not in db_url and "sslmode=" not in db_url:
            separator = "&" if "?" in db_url else "?"
            db_url = f"{db_url}{separator}ssl=require"
    else:
        if "sslmode=" not in db_url and "ssl=" not in db_url:
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
        pool_size=5,
        max_overflow=10,
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
