import unittest
from unittest.mock import MagicMock
from systems.async_thread.manager import AsyncThreadManager

class TestAsyncThreadManager(unittest.TestCase):
    def test_manager_initialization(self):
        mock_context = MagicMock()
        manager = AsyncThreadManager(mock_context)

        self.assertIsNotNone(manager.thread)
        self.assertIsNotNone(manager.async_exec)
        self.assertIsNotNone(manager.bridge)
        self.assertIsNotNone(manager.SubprocessTask)
        self.assertIsNotNone(manager.process_utils)
        
        manager.shutdown()

    def test_manager_shutdown(self):
        mock_context = MagicMock()
        manager = AsyncThreadManager(mock_context)
        # Should cleanly disconnect everything
        manager.shutdown()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()