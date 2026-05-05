import unittest
import os
import json
import tempfile
import shutil
import sys

# Ensure the root is in path before importing internal modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from systems.extension.metadata import MetadataLoader
from systems.extension.dependency_manager import DependencyManager

class TestExtensionSystem(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="elai_ext_test_")
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

    def test_01_metadata_loader_defaults(self):
        """Ensure basic metadata is generated even without metadata.json"""
        ext_path = os.path.join(self.temp_dir, "my_extension")
        os.makedirs(ext_path)
        meta = MetadataLoader.load_metadata(ext_path, "my_extension", is_core=False)
        self.assertEqual(meta["name"], "my_extension")
        self.assertEqual(meta["display_name"], "My Extension")
        self.assertFalse(meta["is_core"])
        self.assertEqual(meta["structure_version"], 1) # default V1

    def test_02_metadata_loader_with_json(self):
        """Test loading from metadata.json and merging with defaults"""
        ext_path = os.path.join(self.temp_dir, "my_extension")
        os.makedirs(ext_path)
        metadata = {"name": "My Extension", "version": "v2.0", "dependencies": ["dev_patcher"]}
        with open(os.path.join(ext_path, "metadata.json"), "w") as f:
            json.dump(metadata, f)

        meta = MetadataLoader.load_metadata(ext_path, "my_extension", is_core=False)
        self.assertEqual(meta["display_name"], "My Extension")
        self.assertEqual(meta["version"], "v2.0")
        self.assertEqual(meta["dependencies"], ["dev_patcher"])

    def test_03_structure_version_detection(self):
        """V2 architecture is detected by presence of gui/windows/core.py"""
        ext_path = os.path.join(self.temp_dir, "v2_ext")
        os.makedirs(os.path.join(ext_path, "gui", "windows"))
        # Actually create the core.py file required by the V2 architecture
        with open(os.path.join(ext_path, "gui", "windows", "core.py"), "w") as f:
            pass
        meta = MetadataLoader.load_metadata(ext_path, "v2_ext", is_core=True)
        self.assertEqual(meta["structure_version"], 2)

    def test_04_dependency_manager_resolve_order(self):
        """Topological sort based on dependencies"""
        ext_meta = {
            "base": {"dependencies": [], "enabled": True},
            "middle": {"dependencies": ["base"], "enabled": True},
            "top": {"dependencies": ["middle", "base"], "enabled": True},
        }
        dep_mgr = DependencyManager(ext_meta)
        order = dep_mgr.resolve_load_order()
        self.assertEqual(order, ["base", "middle", "top"])

    def test_05_dependency_manager_circular_handling(self):
        """Circular dependencies should be broken and conflicting extensions disabled"""
        ext_meta = {
            "a": {"dependencies": ["b"], "enabled": True},
            "b": {"dependencies": ["a"], "enabled": True},
        }
        dep_mgr = DependencyManager(ext_meta)
        order = dep_mgr.resolve_load_order()
        self.assertEqual(len(order), 0) # Both disabled
        self.assertFalse(ext_meta["a"]["enabled"])
        self.assertFalse(ext_meta["b"]["enabled"])

if __name__ == '__main__':
    unittest.main()