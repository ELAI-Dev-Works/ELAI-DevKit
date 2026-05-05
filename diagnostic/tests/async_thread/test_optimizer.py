import unittest
from systems.async_thread.optimizer import ThreadOptimizer

class TestThreadOptimizer(unittest.TestCase):
    def test_optimizer_thread_count(self):
        tc_io = ThreadOptimizer.get_optimal_thread_count(io_bound=True)
        self.assertGreaterEqual(tc_io, 1)
        
        tc_cpu = ThreadOptimizer.get_optimal_thread_count(io_bound=False)
        self.assertGreaterEqual(tc_cpu, 1)

    def test_optimizer_system_load(self):
        load = ThreadOptimizer.get_system_load()
        self.assertIsInstance(load, float)
        self.assertTrue(0.0 <= load <= 100.0)

if __name__ == '__main__':
    unittest.main()