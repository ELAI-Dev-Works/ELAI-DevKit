import os
import shutil
import tempfile
import unittest
from systems.fs.manager import FileSystemManager
from systems.fs.real_fs import RealFileSystem

class TestFSManagerIsolation(unittest.TestCase):
    def setUp(self):
        self.app_root = tempfile.mkdtemp(prefix='elai_fsman_')
        self.project_dir = os.path.join(self.app_root, 'proj')
        os.makedirs(self.project_dir)
        with open(os.path.join(self.project_dir, 'original.txt'), 'w') as f:
            f.write('original')
        self.fs_man = FileSystemManager(self.app_root)

    def tearDown(self):
        shutil.rmtree(self.app_root, ignore_errors=True)

    def test_mount_preserves_real_file(self):
        vfs = self.fs_man.mount_virtual_env(self.project_dir, 'test')
        # File should exist in VFS
        self.assertTrue(vfs.exists('original.txt'))
        # Read should return original content
        self.assertEqual(vfs.read('original.txt'), 'original')
        # Modify in VFS
        vfs.write('original.txt', 'modified')
        self.assertEqual(vfs.read('original.txt'), 'modified')
        # Real file must be unchanged
        with open(os.path.join(self.project_dir, 'original.txt'), 'r') as f:
            self.assertEqual(f.read(), 'original')
        # Unmount
        self.fs_man.unmount_virtual_env()
        self.assertIsNone(self.fs_man.vfs)

    def test_real_fs_is_unaffected_after_unmount(self):
        # Mount, modify, unmount, then check with RealFileSystem
        self.fs_man.mount_virtual_env(self.project_dir, 'test')
        vfs = self.fs_man.vfs
        vfs.write('new.txt', 'hello')
        self.fs_man.unmount_virtual_env()
        real_fs = RealFileSystem(self.project_dir)
        self.assertFalse(real_fs.exists('new.txt'))

if __name__ == '__main__':
    unittest.main()