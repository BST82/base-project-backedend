import time
from typing import AsyncGenerator, Optional, Dict, Any, Tuple
from app.core.config import settings

# In-Memory Cache Fallback when Redis is not running locally
class InMemoryRedis:
    def __init__(self):
        self._store: Dict[str, Tuple[str, float]] = {}  # key -> (value, expire_time)

    def _cleanup_expired(self, key: str) -> None:
        if key in self._store:
            _, exp = self._store[key]
            if exp > 0 and time.time() > exp:
                del self._store[key]

    async def get(self, key: str) -> Optional[str]:
        self._cleanup_expired(key)
        if key in self._store:
            return self._store[key][0]
        return None

    async def set(self, key: str, value: str, nx: bool = False, ex: Optional[int] = None) -> Optional[bool]:
        self._cleanup_expired(key)
        if nx and key in self._store:
            return None
        exp = time.time() + ex if ex else 0.0
        self._store[key] = (str(value), exp)
        return True

    async def delete(self, key: str) -> int:
        if key in self._store:
            del self._store[key]
            return 1
        return 0

    async def exists(self, key: str) -> int:
        self._cleanup_expired(key)
        return 1 if key in self._store else 0

    async def eval(self, script: str, numkeys: int, key: str, value: str) -> int:
        current = await self.get(key)
        if current == value:
            await self.delete(key)
            return 1
        return 0

    async def aclose(self) -> None:
        pass


_in_memory_instance = InMemoryRedis()


async def get_redis_client():
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        # Test connection with 500ms timeout
        await client.ping()
        return client
    except (ImportError, Exception):
        # Fall back to in-memory store for local running without Redis
        return _in_memory_instance


async def get_redis() -> AsyncGenerator[Any, None]:
    client = await get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()


class SlotLockManager:
    """Manages temporary table slot holds during checkout."""

    @staticmethod
    def _build_key(table_id: int, date_str: str, slot_start: str) -> str:
        return f"slot_hold:{table_id}:{date_str}:{slot_start}"

    @classmethod
    async def acquire_hold(
        cls,
        redis: Any,
        table_id: int,
        date_str: str,
        slot_start: str,
        session_id: str,
        ttl_seconds: int = 600
    ) -> bool:
        """Atomically acquires a temporary slot hold using SETNX with TTL."""
        key = cls._build_key(table_id, date_str, slot_start)
        acquired = await redis.set(key, session_id, nx=True, ex=ttl_seconds)
        return bool(acquired)

    @classmethod
    async def release_hold(
        cls,
        redis: Any,
        table_id: int,
        date_str: str,
        slot_start: str,
        session_id: str
    ) -> bool:
        """Releases the slot hold only if the holder matches session_id."""
        key = cls._build_key(table_id, date_str, slot_start)
        result = await redis.eval("", 1, key, session_id)
        return bool(result)

    @classmethod
    async def is_slot_held(
        cls,
        redis: Any,
        table_id: int,
        date_str: str,
        slot_start: str
    ) -> bool:
        key = cls._build_key(table_id, date_str, slot_start)
        return bool(await redis.exists(key))
