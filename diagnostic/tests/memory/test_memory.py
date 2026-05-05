import unittest
import time
from systems.memory.cache import CacheStore
from systems.memory.manager import MemoryManager

class TestMemorySystem(unittest.TestCase):
    def test_01_cache_basic_lru(self):
        cache = CacheStore(max_items=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        
        self.assertEqual(cache.get("a"), 1)  # hit 1
        cache.set("d", 4)  # Should evict 'b' (least recently used)
        
        self.assertIsNone(cache.get("b"))    # miss 1
        self.assertEqual(cache.get("c"), 3)  # hit 2
        self.assertEqual(cache.get("d"), 4)  # hit 3
        self.assertEqual(cache.get("a"), 1)  # hit 4
        
        stats = cache.get_stats()
        self.assertEqual(stats["items_count"], 3)
        self.assertEqual(stats["hits"], 4)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate_percent"], 80.0)

    def test_02_cache_ttl(self):
        cache = CacheStore(max_items=10)
        cache.set("a", 1, ttl=0.1)
        self.assertTrue(cache.has("a"))
        self.assertEqual(cache.get("a"), 1)
        
        time.sleep(0.15)
        self.assertFalse(cache.has("a"))
        self.assertIsNone(cache.get("a"))

    def test_03_get_or_compute(self):
        cache = CacheStore(max_items=10)
        call_count = 0
        
        def compute_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
            
        # Due to the fixed signature, kwargs for the cache must be explicit, while the rest flows to *args
        res1 = cache.get_or_compute("calc_10", compute_func, 10, ttl=None, tags=None, size=None)
        self.assertEqual(res1, 20)
        self.assertEqual(call_count, 1)
        
        res2 = cache.get_or_compute("calc_10", compute_func, 10)
        self.assertEqual(res2, 20)
        self.assertEqual(call_count, 1)  # Function not called again

    def test_04_manager_domains(self):
        manager = MemoryManager("/dummy/path")
        cache1 = manager.get_cache("domain1")
        cache2 = manager.get_cache("domain2")
        
        cache1.set("key", "val1")
        cache2.set("key", "val2")
        
        self.assertEqual(cache1.get("key"), "val1")
        self.assertEqual(cache2.get("key"), "val2")
        
        manager.clear_domain("domain1")
        self.assertIsNone(cache1.get("key"))
        self.assertEqual(cache2.get("key"), "val2")

    def test_05_memoize_decorator(self):
        manager = MemoryManager("/dummy/path")
        call_count = 0
        
        @manager.memoize("math_ops")
        def expensive_calc(a, b):
            nonlocal call_count
            call_count += 1
            return a + b
            
        self.assertEqual(expensive_calc(2, 3), 5)
        self.assertEqual(call_count, 1)
        
        self.assertEqual(expensive_calc(2, 3), 5)
        self.assertEqual(call_count, 1)  # Cached
        
        self.assertEqual(expensive_calc(3, 4), 7)
        self.assertEqual(call_count, 2)  # New arguments, new call

    def test_06_cache_size_limit(self):
        cache = CacheStore(max_items=10, max_size_bytes=100)
        cache.set("a", "data_A", size=40)
        cache.set("b", "data_B", size=40)
        self.assertEqual(cache.get_stats()["current_size_bytes"], 80)
        
        cache.set("c", "data_C", size=40)
        # Should evict 'a' because 80 + 40 = 120 > 100
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), "data_B")
        self.assertEqual(cache.get("c"), "data_C")
        self.assertEqual(cache.get_stats()["current_size_bytes"], 80)

    def test_07_cache_tags(self):
        cache = CacheStore(max_items=10)
        cache.set("k1", "v1", tags=["groupA"])
        cache.set("k2", "v2", tags=["groupA", "groupB"])
        cache.set("k3", "v3", tags=["groupB"])
        
        self.assertTrue(cache.has("k1"))
        self.assertTrue(cache.has("k2"))
        self.assertTrue(cache.has("k3"))
        
        cache.invalidate_by_tag("groupA")
        
        self.assertFalse(cache.has("k1"))
        self.assertFalse(cache.has("k2"))
        self.assertTrue(cache.has("k3"))

    def test_08_eviction_callback(self):
        evicted_items =[]
        def on_evict(key, value):
            evicted_items.append((key, value))
            
        cache = CacheStore(max_items=2, on_evict=on_evict)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3") # Should evict k1
        
        self.assertEqual(len(evicted_items), 1)
        self.assertEqual(evicted_items[0], ("k1", "v1"))
        
        cache.clear() # Should evict k2 and k3
        self.assertEqual(len(evicted_items), 3)
        self.assertIn(("k2", "v2"), evicted_items)
        self.assertIn(("k3", "v3"), evicted_items)

    def test_09_pattern_deletion(self):
        cache = CacheStore(max_items=10)
        cache.set("user:1:name", "Alice")
        cache.set("user:2:name", "Bob")
        cache.set("product:1:name", "Laptop")
        
        cache.delete_pattern(r"^user:\d+:name$")
        
        self.assertFalse(cache.has("user:1:name"))
        self.assertFalse(cache.has("user:2:name"))
        self.assertTrue(cache.has("product:1:name"))

    def test_10_disk_persistence(self):
        import tempfile
        import shutil
        import os

        temp_app_root = tempfile.mkdtemp(prefix="elai_mem_app_")
        try:
            manager = MemoryManager(temp_app_root)
            manager.current_project_path = os.path.join(temp_app_root, "test_proj")

            cache = manager.get_cache("patch_plans")
            cache.set("plan_1", "plan_data")

            manager.save_to_disk()

            manager2 = MemoryManager(temp_app_root)
            manager2.current_project_path = os.path.join(temp_app_root, "test_proj")
            manager2.load_from_disk()

            cache2 = manager2.get_cache("patch_plans")
            self.assertEqual(cache2.get("plan_1"), "plan_data")

            manager2.cleanup_temp_cache()
            self.assertFalse(os.path.exists(manager2._get_cache_file()))
        finally:
            shutil.rmtree(temp_app_root, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()