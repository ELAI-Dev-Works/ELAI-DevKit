import unittest
import os
import shutil
import tempfile
from systems.fs.base_fs import BaseFileSystem
from systems.fs.vfs_core import AdvancedVFS
from systems.fs.manager import FileSystemManager
from systems.project.ignore_handler import IgnoreHandler

class TestFileSystem(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="elai_test_fs_")
        self.project_dir = os.path.join(self.test_dir, "project")
        os.makedirs(self.project_dir)
        with open(os.path.join(self.project_dir, "file.txt"), "w") as f:
            f.write("original")
            
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_base_fs_security(self):
        base_fs = BaseFileSystem(self.project_dir)
        # Valid paths
        self.assertEqual(base_fs._to_abs("@ROOT/file.txt"), os.path.join(self.project_dir, "file.txt").replace('\\', '/'))
        self.assertEqual(base_fs._to_abs("file.txt"), os.path.join(self.project_dir, "file.txt").replace('\\', '/'))
        
        # Security violations
        with self.assertRaises(PermissionError):
            base_fs._to_abs("../outside.txt")
        with self.assertRaises(ValueError):
            base_fs._to_abs(os.path.abspath(os.path.join(self.test_dir, "outside.txt")))

    def test_advanced_vfs_cow_and_clone(self):
        vfs = AdvancedVFS(self.project_dir)

        # Test Mounting
        vfs.mount(IgnoreHandler([],[]))
        self.assertTrue(vfs.exists("file.txt"))
        self.assertEqual(vfs.read("file.txt"), "original")
        
        # Test Copy-on-Write (Modification)
        vfs.write("file.txt", "modified")
        self.assertEqual(vfs.read("file.txt"), "modified")
        
        # Verify original is untouched
        with open(os.path.join(self.project_dir, "file.txt"), "r") as f:
            self.assertEqual(f.read(), "original")
            
        # Verify modified marker
        self.assertIn(vfs._to_abs("file.txt"), vfs.modified_paths)
        
        # Test Cloning
        clone_vfs = vfs.clone()
        self.assertTrue(clone_vfs.exists("file.txt"))
        self.assertEqual(clone_vfs.read("file.txt"), "modified")
        self.assertIn(clone_vfs._to_abs("file.txt"), clone_vfs.modified_paths)
        
        # Test Unmount
        vfs.unmount()
        clone_vfs.unmount()

    def test_fs_manager(self):
        manager = FileSystemManager(self.test_dir)
        self.assertFalse(manager.is_virtual())
        
        vfs = manager.mount_virtual_env(self.project_dir, "test_session")
        self.assertTrue(manager.is_virtual())
        self.assertIsNotNone(manager.vfs)
        
        manager.unmount_virtual_env()
        self.assertFalse(manager.is_virtual())
        self.assertIsNone(manager.vfs)

if __name__ == '__main__':
    unittest.main()