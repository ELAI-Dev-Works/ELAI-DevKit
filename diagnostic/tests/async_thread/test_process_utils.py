import unittest
import subprocess
import sys
from systems.async_thread.process_utils import ProcessManager

class TestProcessUtils(unittest.TestCase):
    def test_get_creation_flags(self):
        flags = ProcessManager.get_creation_flags()
        self.assertIsInstance(flags, int)
        if sys.platform == 'win32':
            self.assertEqual(flags, subprocess.CREATE_NO_WINDOW)
        else:
            self.assertEqual(flags, 0)

    def test_kill_process_tree(self):
        # Safe to kill a non-existent PID, shouldn't raise errors
        ProcessManager.kill_process_tree(-9999)
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()