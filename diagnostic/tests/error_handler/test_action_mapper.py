import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from systems.error_handler.action_mapper import ActionMapper
from systems.error_handler.debug import DEBUG_MODE, set_debug_mode

class TestActionMapper(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_root = ActionMapper._instance.root_path if ActionMapper._instance else None
        ActionMapper._instance = None

    def tearDown(self):
        if ActionMapper._instance:
            ActionMapper._instance.is_running = False
        ActionMapper._instance = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('systems.error_handler.action_mapper.open')
    @patch('systems.error_handler.action_mapper.getattr')
    def test_start_flush_and_stop(self, mock_getattr, mock_open):
        """Ensure start, flush, and get_current_map work and gracefully handle no log file."""
        ActionMapper._instance = None

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = "[ACTIONS MAP] - Session Start\n"

        # Temporarily enable DEBUG_MODE so that profiling actually runs
        old_debug = DEBUG_MODE
        set_debug_mode(True)
        try:
            ActionMapper.start(clear_log=True)
            instance = ActionMapper._instance
            self.assertTrue(instance.is_running)
            # Add some fake actions to ensure flush writes something
            instance.actions = ["<test.py> funcA -> funcB -> "]
            ActionMapper.flush()
            # Retrieve map (should contain the header we wrote on start)
            map_str = ActionMapper.get_current_map()
            self.assertIn("[ACTIONS MAP]", map_str)
            instance.is_running = False
        finally:
            set_debug_mode(old_debug)
        ActionMapper._instance = None

    def test_flush_empty_actions_no_file(self):
        """Flush with an empty actions list and missing log file should not crash."""
        instance = ActionMapper()
        instance.log_path = os.path.join(self.temp_dir, 'nonexistent', 'run_log.txt')
        instance.actions = []
        # Should not raise
        ActionMapper.flush()

if __name__ == '__main__':
    unittest.main()