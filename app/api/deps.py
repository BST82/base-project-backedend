from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import decode_access_token
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """Validate JWT access token and return the authenticated user."""
    if token:
        try:
            payload = decode_access_token(token)
            if payload and payload.get("sub"):
                user_id = int(payload.get("sub"))
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if user:
                    if not user.is_active:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Account is deactivated"
                        )
                    return user
        except HTTPException:
            raise
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please sign in.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_current_user(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """Return user if valid token provided; otherwise None without raising 401."""
    if token:
        try:
            payload = decode_access_token(token)
            if payload and payload.get("sub"):
                user_id = int(payload.get("sub"))
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if user and user.is_active:
                    return user
        except Exception:
            pass
    return None


async def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """RBAC Enforcement: verify that the authenticated user possesses the ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required. Access denied."
        )
    return current_user


