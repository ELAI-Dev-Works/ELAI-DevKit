import os
from typing import Optional
from .vfs_core import AdvancedVFS

class FileSystemManager:
    """
    Global File System Manager for ELAI-DevKit.
    Provides a unified API and manages the isolated Workspace Sandbox.
    """
    def __init__(self, app_root_path: str):
        self.app_root_path = app_root_path
        self.workspace_base = os.path.join(self.app_root_path, 'user', 'vfs_workspace')
        os.makedirs(self.workspace_base, exist_ok=True)

        # Active virtual file system (None if we interact with real OS files directly)
        self.vfs: Optional[AdvancedVFS] = None
        self.memory = None
    
    def mount_virtual_env(self, target_project_path: str, session_id: str = "default_session") -> AdvancedVFS:
        """Mounts a project into an isolated in-memory VFS."""
        self.vfs = AdvancedVFS(target_project_path)
        self.vfs.memory = self.memory
        self.vfs.mount()
        return self.vfs
        
    def unmount_virtual_env(self):
        """Unmounts the current VFS and cleans up."""
        if self.vfs:
            self.vfs.unmount()
            self.vfs = None
            
    def is_virtual(self) -> bool:
        """Returns True if the system is currently using the isolated Sandbox."""
        return self.vfs is not None

    def get_fs(self, root_path: str):
        """
        Unified wrapper method that automatically routes to `self.vfs` if virtual and matches root,
        or returns a cached `RealFileSystem` for the target path.
        """
        from .real_fs import RealFileSystem
        if not root_path: return None
        norm_root = os.path.abspath(root_path).replace('\\', '/')
        if self.vfs and self.vfs.root == norm_root:
            return self.vfs

        if not hasattr(self, '_real_fs_cache'):
            self._real_fs_cache = {}

        if norm_root not in self._real_fs_cache:
            rfs = RealFileSystem(norm_root)
            rfs.memory = self.memory
            self._real_fs_cache[norm_root] = rfs
        return self._real_fs_cache[norm_root]
    # that automatically route to `self.vfs.read()` if virtual, or `os/shutil` if real.