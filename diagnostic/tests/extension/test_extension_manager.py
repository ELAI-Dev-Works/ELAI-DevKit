import unittest
import os
import sys
import tempfile
import shutil
import json
from unittest.mock import MagicMock, patch

# Make sure root is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from systems.extension.manager import ExtensionManager

class TestExtensionManager(unittest.TestCase):
    def setUp(self):
        self.temp_root = tempfile.mkdtemp()
        self.app_root = os.path.join(self.temp_root, "app")
        os.makedirs(os.path.join(self.app_root, "apps"))
        os.makedirs(os.path.join(self.app_root, "extensions", "custom_apps"))
        # Mock MainWindow
        self.mw = MagicMock()
        self.mw.app_root_path = self.app_root
        self.mw.settings_manager.get_setting.return_value = {}
        self.mw.extension_manager = None  # will be replaced

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _create_extension(self, folder_name, is_core=True, has_gui=False):
        base = os.path.join(self.app_root, "apps") if is_core else os.path.join(self.app_root, "extensions", "custom_apps")
        ext_path = os.path.join(base, folder_name)
        os.makedirs(ext_path)
        # Create minimal app.py
        with open(os.path.join(ext_path, "app.py"), 'w') as f:
            f.write("class {}App:\n    def __init__(self, ctx): pass\n".format("".join(p.capitalize() for p in folder_name.split('_'))))
        if has_gui:
            os.makedirs(os.path.join(ext_path, "gui", "windows"))
            with open(os.path.join(ext_path, "gui", "windows", "core.py"), 'w') as f:
                f.write("class {}CoreWindow:\n    pass\n".format("".join(p.capitalize() for p in folder_name.split('_'))))
        # Metadata is optional; discovery will generate default

    def test_discover_and_load_basic(self):
        self._create_extension("test_ext", is_core=True, has_gui=True)
        mgr = ExtensionManager(self.mw)
        mgr.discover_extensions()
        self.assertIn("test_ext", mgr.extensions)
        meta = mgr.extensions["test_ext"]
        self.assertTrue(meta["is_core"])
        self.assertEqual(meta["structure_version"], 2)  # has gui/windows/core.py
        # Load and initialize
        mgr.load_extensions()
        mgr.initialize_extensions()
        self.assertTrue(meta["enabled"])
        self.assertIsNotNone(meta["instance"])
        # GUI widget class should be present
        self.assertIsNotNone(meta.get("gui_class"))

    def test_discover_fails_on_missing_app_py(self):
        # Create directory without app.py
        base = os.path.join(self.app_root, "apps", "bad_ext")
        os.makedirs(base)
        mgr = ExtensionManager(self.mw)
        mgr.discover_extensions()
        self.assertNotIn("bad_ext", mgr.extensions)

if __name__ == '__main__':
    unittest.main()