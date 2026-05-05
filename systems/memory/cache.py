import time
import sys
import re
from collections import OrderedDict
from typing import Any, Optional, Callable, List, Set

class CacheItem:
    __slots__ =['value', 'expires_at', 'tags', 'size']
    
    def __init__(self, value: Any, ttl: Optional[float] = None, tags: Optional[List[str]] = None, size: int = 0):
        self.value = value
        self.expires_at = time.time() + ttl if ttl else None
        self.tags = set(tags) if tags else set()
        self.size = size

    def is_expired(self) -> bool:
        return self.expires_at is not None and time.time() > self.expires_at

class CacheStore:
    """
    An advanced LRU cache implementation supporting TTL, lazy compute, tags, memory limits, and eviction callbacks.
    """
    def __init__(self, max_items: int = 1000, max_size_bytes: Optional[int] = None, on_evict: Optional[Callable[[str, Any], None]] = None):
        self.max_items = max_items
        self.max_size_bytes = max_size_bytes
        self.on_evict = on_evict
        self._cache = OrderedDict()
        self._tag_index = {}
        self._current_size = 0
        self._hits = 0
        self._misses = 0

    def _evict(self, key: str):
        """Internal method to cleanly remove an item, deduct its size, and clean up tags."""
        if key in self._cache:
            item = self._cache.pop(key)
            self._current_size -= item.size
            for tag in item.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(key)
                    if not self._tag_index[tag]:
                        del self._tag_index[tag]
            if self.on_evict:
                try:
                    self.on_evict(key, item.value)
                except Exception:
                    pass # Eviction callbacks should not crash the cache

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            item = self._cache[key]
            if item.is_expired():
                self._evict(key)
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return item.value
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None, tags: Optional[List[str]] = None, size: Optional[int] = None):
        if key in self._cache:
            self._evict(key)

        # Do not trust sys.getsizeof for complex/nested objects.
        # Only track size if explicitly provided by the caller (like real_fs.py does with len()).
        item_size = size if size is not None else 0
        item = CacheItem(value, ttl, tags, item_size)
        
        self._cache[key] = item
        self._current_size += item_size
        
        if tags:
            for tag in tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(key)
                
        # Enforce limits (Count and Size)
        while self._cache and ((self.max_items and len(self._cache) > self.max_items) or (self.max_size_bytes and self._current_size > self.max_size_bytes)):
            lru_key = next(iter(self._cache))
            self._evict(lru_key)

    def delete(self, key: str):
        self._evict(key)

    def delete_pattern(self, pattern: str):
        """Removes all items whose keys match the given regex pattern."""
        regex = re.compile(pattern)
        keys_to_delete =[k for k in self._cache.keys() if regex.match(k)]
        for k in keys_to_delete:
            self._evict(k)

    def clear(self):
        # Iterate and evict to ensure callbacks are fired
        keys = list(self._cache.keys())
        for key in keys:
            self._evict(key)
        self._hits = 0
        self._misses = 0

    def has(self, key: str) -> bool:
        """Checks if a valid, unexpired key exists in the cache without affecting LRU order."""
        if key in self._cache:
            if not self._cache[key].is_expired():
                return True
            self._evict(key)
        return False

    def invalidate_by_tag(self, tag: str):
        """Removes all cache items associated with the given tag."""
        if tag in self._tag_index:
            keys_to_delete = list(self._tag_index[tag])
            for k in keys_to_delete:
                self._evict(k)

    def get_or_compute(self, key: str, compute_func: Callable, *args, ttl: Optional[float] = None, tags: Optional[List[str]] = None, size: Optional[int] = None, **kwargs) -> Any:
        """
        Retrieves the value from cache. If not found or expired, computes it using compute_func,
        stores it, and returns the new value.
        """
        if self.has(key):
            return self.get(key)
        
        val = compute_func(*args, **kwargs)
        self.set(key, val, ttl=ttl, tags=tags, size=size)
        return val

    def get_stats(self) -> dict:
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests) * 100.0 if total_requests > 0 else 0.0
        return {
            "items_count": len(self._cache),
            "current_size_bytes": self._current_size,
            "max_items": self.max_items,
            "max_size_bytes": self.max_size_bytes,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2)
        }