import unittest
import sys
import shutil
from systems.fs.os_bridge.sandbox import OSSandbox

class TestOSSandbox(unittest.TestCase):
    def test_wrap_command_trusted(self):
        cmd = ["echo", "hello"]
        wrapped = OSSandbox.wrap_command(cmd, "/tmp", is_trusted=True)
        self.assertEqual(wrapped, cmd)

    def test_wrap_command_untrusted_linux(self):
        if sys.platform == 'linux':
            cmd = ["echo", "hello"]
            if shutil.which('bwrap'):
                wrapped = OSSandbox.wrap_command(cmd, "/tmp", is_trusted=False)
                self.assertIn('bwrap', wrapped)
                self.assertIn('--ro-bind', wrapped)

    def test_wrap_command_untrusted_darwin(self):
        if sys.platform == 'darwin':
            cmd = ["echo", "hello"]
            if shutil.which('sandbox-exec'):
                wrapped = OSSandbox.wrap_command(cmd, "/tmp", is_trusted=False)
                self.assertIn('sandbox-exec', wrapped)
                self.assertIn('-f', wrapped)

    def test_wrap_command_untrusted_windows(self):
        if sys.platform == 'win32':
            cmd = ["echo", "hello"]
            wrapped = OSSandbox.wrap_command(cmd, "/tmp", is_trusted=False)
            self.assertEqual(wrapped, cmd)

if __name__ == '__main__':
    unittest.main()