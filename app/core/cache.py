import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached value with its expiration timestamp."""

    value: Any
    expires_at: float


class TTLCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl_seconds: int = 60) -> None:
        self._ttl_seconds = ttl_seconds
        self._data: dict[str, CacheEntry] = {}

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Store a value with TTL."""

        self._data[key] = CacheEntry(
            value=value,
            expires_at=(
                time.monotonic()
                + self._ttl_seconds
            ),
        )

    def delete(self, key: str) -> None:
        """Remove a cached value."""

        self._data.pop(key, None)

    def clear(self) -> None:
        """Clear the entire cache."""

        self._data.clear()

    def get(self, key: str) -> Any | None:
        """Return cached value if present and not expired."""

        entry = self._data.get(key)

        if entry is None:
            logger.debug(
                "Cache MISS: key=%s",
                key,
            )
            return None

        if time.monotonic() >= entry.expires_at:
            del self._data[key]

            logger.debug(
                "Cache EXPIRED: key=%s",
                key,
            )

            return None

        logger.debug(
            "Cache HIT: key=%s",
            key,
        )

        return entry.value
