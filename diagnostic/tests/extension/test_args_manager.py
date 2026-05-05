import unittest
import sys
import os
import argparse
from unittest.mock import MagicMock, patch

class TestArgsManager(unittest.TestCase):
    def setUp(self):
        self.mw = MagicMock()
        self.mw.app_root_path = os.getcwd()
        self.mw.root_path = None
        self.mw.extension_manager = MagicMock()
        self.mw.extension_manager.extensions = {}
        self.mw.settings_manager = MagicMock()

    def test_01_no_args(self):
        from systems.extension.args import ArgsManager
        with patch.object(sys, 'argv', ['launch.py']):
            am = ArgsManager(self.mw)
            handled, should_exit = am.parse_and_handle()
            self.assertFalse(handled)
            self.assertFalse(should_exit)

    def test_02_extension_handler_returns_tuple(self):
        from systems.extension.args import ArgsManager

        ext_mock = {
            "test_ext": {
                "enabled": True,
                "is_core": True,
                "path": "/tmp"
            }
        }
        self.mw.extension_manager.extensions = ext_mock

        handler_module = MagicMock()
        handler_module.register_args = MagicMock()
        handler_module.handle_args = MagicMock(return_value=(True, False))

        with patch('importlib.util.spec_from_file_location'), \
             patch('importlib.util.module_from_spec', return_value=handler_module), \
             patch('os.path.exists', return_value=True), \
             patch.object(sys, 'argv', ['launch.py', '--test']), \
             patch('sys.exit') as mock_exit:
            am = ArgsManager(self.mw)
            # Manually inject the handler
            am.extension_handlers["test_ext"] = handler_module.handle_args
            handled, should_exit = am.parse_and_handle()
            self.assertTrue(handled)
            self.assertFalse(should_exit)

if __name__ == '__main__':
    unittest.main()