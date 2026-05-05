from typing import Dict, Callable, Optional, Any, List
from functools import wraps
import hashlib
import os
import pickle
from .cache import CacheStore

class MemoryManager:
    """
    Global Memory and Caching System for ELAI-DevKit.
    Manages multiple cache domains (e.g., 'patch_plans', 'vfs_reads', 'ast_trees').
    """
    def __init__(self, app_root_path: str):
        self.app_root_path = app_root_path
        self.domains: Dict[str, CacheStore] = {}

    def get_cache(self, domain: str, max_items: int = 1000, max_size_bytes: Optional[int] = None, on_evict: Optional[Callable] = None) -> CacheStore:
        """
        Retrieves an existing cache domain or creates a new one.
        """
        if domain not in self.domains:
            self.domains[domain] = CacheStore(max_items=max_items, max_size_bytes=max_size_bytes, on_evict=on_evict)
        return self.domains[domain]

    def clear_domain(self, domain: str):
        """Clears a specific cache domain."""
        if domain in self.domains:
            self.domains[domain].clear()

    def clear_all(self):
        """Clears all caches across all domains. Useful for hard resets or releasing memory."""
        for cache_store in self.domains.values():
            cache_store.clear()

    def invalidate_by_tag(self, domain: str, tag: str):
        """Invalidates items in a specific domain by tag."""
        if domain in self.domains:
            self.domains[domain].invalidate_by_tag(tag)

    def invalidate_all_by_tag(self, tag: str):
        """Invalidates items matching the tag across ALL domains."""
        for cache_store in self.domains.values():
            cache_store.invalidate_by_tag(tag)

    def get_all_stats(self) -> Dict[str, dict]:
        """Returns statistics for all cache domains."""
        return {domain: cache.get_stats() for domain, cache in self.domains.items()}

    def _get_cache_file(self) -> Optional[str]:
        # Tries to determine the project path by analyzing domains or injecting state from outside.
        # However, a cleaner way is if we have the current project path. MemoryManager can deduce it.
        # We will expose it via an attribute set by MainWindow.
        if not hasattr(self, 'current_project_path') or not self.current_project_path:
            return None
        project_name = os.path.basename(os.path.normpath(self.current_project_path))
        path_hash = hashlib.md5(self.current_project_path.encode('utf-8')).hexdigest()[:8]
        return os.path.join(self.app_root_path, 'user', 'projects', f"{project_name}_{path_hash}", 'cache', 'memory.pkl')

    def save_to_disk(self):
        """Saves essential cache domains to disk for persistence."""
        cache_file = self._get_cache_file()
        if not cache_file: return
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        try:
            data_to_save = {}
            # Only save file reads and patch plans to avoid saving volatile data
            for domain in ['fs_reads', 'fs_reads_bytes', 'patch_plans']:
                if domain in self.domains:
                    data_to_save[domain] = self.domains[domain]._cache

            if data_to_save:
                with open(cache_file, 'wb') as f:
                    pickle.dump(data_to_save, f)
        except Exception as e:
            print(f"[MemoryManager] Failed to save cache to disk: {e}")

    def load_from_disk(self):
        """Loads cached domains from disk."""
        cache_file = self._get_cache_file()
        if not cache_file or not os.path.exists(cache_file): return
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)

            for domain, cache_dict in data.items():
                store = self.get_cache(domain)
                store._cache = cache_dict
                # Recalculate size
                store._current_size = sum(item.size for item in cache_dict.values())

            self.sync_cache()

        except Exception as e:
            print(f"[MemoryManager] Failed to load cache from disk: {e}")
            self.cleanup_temp_cache()


    def sync_cache(self):
        """Synchronizes cache with the physical file system to remove stale data."""
        if not self.current_project_path: return
        for domain in['fs_reads', 'fs_reads_bytes']:
            if domain in self.domains:
                cache_store = self.domains[domain]
                keys_to_evict =[]
                for key, item in list(cache_store._cache.items()):
                    if key.startswith("rfs_read:") or key.startswith("rfs_read_bytes:"):
                        abs_path = key.split(":", 1)[1]
                        if not os.path.exists(abs_path):
                            keys_to_evict.append(key)
                        else:
                            try:
                                mtime = os.path.getmtime(abs_path)
                                fsize = os.path.getsize(abs_path)
                                if item.value.get('mtime') != mtime or item.value.get('fsize') != fsize:
                                    keys_to_evict.append(key)
                            except OSError:
                                keys_to_evict.append(key)
                for key in keys_to_evict:
                    cache_store.delete(key)

    def cleanup_temp_cache(self):
        """Deletes the cache file if persistent caching is disabled."""
        cache_file = self._get_cache_file()
        if cache_file and os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except OSError:
                pass


    def generate_key(self, *args, **kwargs) -> str:
        """Generates a stable string key from arguments."""
        key_str = f"{args}:{kwargs}"
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()

    def memoize(self, domain: str, max_items: int = 1000, max_size_bytes: Optional[int] = None, ttl: Optional[float] = None, key_func: Callable = None, tags: Optional[List[str]] = None):
        """
        Decorator to easily cache the results of a method or function.
        """
        cache_store = self.get_cache(domain, max_items=max_items, max_size_bytes=max_size_bytes)
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Simple default key generation. 
                    # Note: For methods, 'args[0]' is usually 'self', which might not have a clean string representation.
                    # It's recommended to provide a custom key_func for complex class methods.
                    key_str = f"{func.__module__}.{func.__qualname__}:{args}:{kwargs}"
                    cache_key = hashlib.md5(key_str.encode('utf-8')).hexdigest()
                
                return cache_store.get_or_compute(cache_key, func, *args, ttl=ttl, tags=tags, size=None, **kwargs)
            return wrapper
        return decorator