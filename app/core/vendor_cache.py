from app.core.cache import TTLCache
vendor_cache = TTLCache(
    ttl_seconds=60,
)