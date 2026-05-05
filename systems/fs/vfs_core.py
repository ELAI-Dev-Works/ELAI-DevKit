import os
import shutil
import posixpath
import uuid
from .base_fs import BaseFileSystem

class AdvancedVFS(BaseFileSystem):
    """
    Advanced Virtual File System with Copy-on-Write (CoW) support.
    Operates entirely in-memory for high-performance simulations.
    """
    def __init__(self, real_root: str):
        super().__init__(real_root)
        self.is_mounted = False
        self.modified_paths = set()
        self.files = {}      # abs_path -> content (str or bytes)
        self.folders = set() # abs_path
        self.deleted = set() # abs_path
        self.ignore_handler = None

    def mount(self, ignore_handler=None):
        self.ignore_handler = ignore_handler
        self.is_mounted = True

    def unmount(self):
        self.files.clear()
        self.folders.clear()
        self.deleted.clear()
        self.modified_paths.clear()
        self.is_mounted = False

    def clone(self):
        """Creates a fast isolated clone of the current in-memory sandbox."""
        new_vfs = self.__class__.__new__(self.__class__)
        new_vfs.root = self.root
        new_vfs.is_mounted = self.is_mounted
        new_vfs.modified_paths = set(self.modified_paths)
        new_vfs.files = dict(self.files)
        new_vfs.folders = set(self.folders)
        new_vfs.deleted = set(self.deleted)
        
        if hasattr(self, 'ignore_handler'):
            new_vfs.ignore_handler = self.ignore_handler
        if hasattr(self, 'memory'):
            new_vfs.memory = self.memory
            
        return new_vfs

    def _is_deleted(self, abs_path: str) -> bool:
        """Checks if a path or any of its parents are marked as deleted."""
        if abs_path in self.deleted: 
            return True
        parent = posixpath.dirname(abs_path)
        while parent and parent != self.root and parent != abs_path:
            if parent in self.deleted: 
                return True
            parent = posixpath.dirname(parent)
        return False

    def _mark_modified(self, virtual_path: str):
        self.modified_paths.add(self._to_abs(virtual_path))

    # --- File System API ---

    def exists(self, path: str) -> bool:
        abs_path = self._to_abs(path)
        if self._is_deleted(abs_path): return False
        if abs_path in self.files or abs_path in self.folders: return True
        return os.path.exists(abs_path)

    def is_dir(self, path: str) -> bool:
        abs_path = self._to_abs(path)
        if self._is_deleted(abs_path): return False
        if abs_path in self.folders: return True
        if abs_path in self.files: return False
        return os.path.isdir(abs_path)

    def listdir(self, path: str) -> list:
        # Relies on our custom walk
        abs_path = self._to_abs(path)
        for r, ds, fs in self.walk(path):
            if r == abs_path:
                return ds + fs
        raise FileNotFoundError(f"No such directory: {abs_path}")

    def read(self, path: str) -> str:
        abs_path = self._to_abs(path)
        if self._is_deleted(abs_path): raise FileNotFoundError(f"File deleted in VFS: {abs_path}")
        
        if abs_path in self.files:
            c = self.files[abs_path]
            return c.decode('utf-8', errors='ignore') if isinstance(c, bytes) else c

        # Fallback to real FS with Memory cache
        from systems.fs.real_fs import RealFileSystem
        rfs = RealFileSystem(self.root)
        rfs.memory = self.memory
        return rfs.read(path)

    def read_bytes(self, path: str) -> bytes:
        abs_path = self._to_abs(path)
        if self._is_deleted(abs_path): raise FileNotFoundError(f"File deleted in VFS: {abs_path}")
        
        if abs_path in self.files:
            c = self.files[abs_path]
            return c if isinstance(c, bytes) else c.encode('utf-8')

        # Fallback to real FS with Memory cache
        from systems.fs.real_fs import RealFileSystem
        rfs = RealFileSystem(self.root)
        rfs.memory = self.memory
        return rfs.read_bytes(path)

    def write(self, path: str, content: str):
        if isinstance(content, bytes):
            raise TypeError("write expects str, received bytes.")
        abs_path = self._to_abs(path)
        self._ensure_parents(abs_path)
        self.files[abs_path] = content
        self.modified_paths.add(abs_path)
        if abs_path in self.deleted: self.deleted.remove(abs_path)

    def write_bytes(self, path: str, content: bytes):
        abs_path = self._to_abs(path)
        self._ensure_parents(abs_path)
        self.files[abs_path] = content
        self.modified_paths.add(abs_path)
        if abs_path in self.deleted: self.deleted.remove(abs_path)

    def delete(self, path: str):
        abs_path = self._to_abs(path)
        self.deleted.add(abs_path)
        self.modified_paths.add(abs_path)
        if abs_path in self.files: del self.files[abs_path]
        if abs_path in self.folders: self.folders.remove(abs_path)

    def makedirs(self, path: str):
        abs_path = self._to_abs(path)
        self._ensure_parents(abs_path, include_self=True)

    def _ensure_parents(self, abs_path, include_self=False):
        p = abs_path if include_self else posixpath.dirname(abs_path)
        while p and p != self.root and p not in self.folders:
            self.folders.add(p)
            if p in self.deleted: self.deleted.remove(p)
            self.modified_paths.add(p)
            p = posixpath.dirname(p)

    def _copy_tree_to_memory(self, abs_src, abs_dst):
        self.makedirs(abs_dst)
        for r, ds, fs in self.walk(abs_src):
            rel_r = posixpath.relpath(r, abs_src)
            target_r = posixpath.join(abs_dst, rel_r) if rel_r != '.' else abs_dst
            self.makedirs(target_r)
            for f in fs:
                src_f = posixpath.join(r, f)
                dst_f = posixpath.join(target_r, f)
                self.write_bytes(dst_f, self.read_bytes(src_f))

    def move(self, src: str, dst: str):
        abs_src = self._to_abs(src)

        # If dst is an existing directory, move INTO it.
        if self.is_dir(dst):
            dst = posixpath.join(dst, posixpath.basename(abs_src))

        self.copy(src, dst)
        self.delete(src)

    def copy(self, src: str, dst: str):
        abs_src = self._to_abs(src)
        abs_dst = self._to_abs(dst)
        if self.is_dir(src):
            self._copy_tree_to_memory(abs_src, abs_dst)
        else:
            if self.is_dir(dst):
                dst = posixpath.join(dst, posixpath.basename(abs_src))
            self.write_bytes(dst, self.read_bytes(src))

    def rename(self, src: str, dst: str):
        self.move(src, dst)

    def walk(self, top: str):
        abs_top = self._to_abs(top)
        tree = {}
        def ensure_dir(d):
            if d not in tree: tree[d] = (set(), set())

        # 1. Real FS traversal
        if os.path.exists(abs_top) and not self._is_deleted(abs_top):
            for r, ds, fs in os.walk(abs_top):
                r = r.replace('\\', '/')
                if self._is_deleted(r):
                    ds.clear()
                    continue
                if self.ignore_handler and self.ignore_handler.is_ignored(posixpath.basename(r), is_dir=True):
                    ds.clear()
                    continue

                ensure_dir(r)
                
                # Verify and add subdirs
                for d in ds:
                    d_abs = posixpath.join(r, d)
                    if not self._is_deleted(d_abs):
                        if not (self.ignore_handler and self.ignore_handler.is_ignored(d, is_dir=True)):
                            tree[r][0].add(d)
                
                # Verify and add files
                for f in fs:
                    f_abs = posixpath.join(r, f)
                    if not self._is_deleted(f_abs):
                        if not (self.ignore_handler and self.ignore_handler.is_ignored(f, is_dir=False)):
                            tree[r][1].add(f)

        # 2. Virtual FS traversal
        for f in self.files.keys():
            if f.startswith(abs_top):
                if self.ignore_handler and self.ignore_handler.is_ignored(posixpath.basename(f), is_dir=False): 
                    continue
                p = posixpath.dirname(f)
                ensure_dir(p)
                tree[p][1].add(posixpath.basename(f))
                while p != abs_top and p.startswith(abs_top):
                    parent = posixpath.dirname(p)
                    ensure_dir(parent)
                    tree[parent][0].add(posixpath.basename(p))
                    p = parent

        for d in self.folders:
            if d.startswith(abs_top) and d != abs_top:
                if self.ignore_handler and self.ignore_handler.is_ignored(posixpath.basename(d), is_dir=True): 
                    continue
                p = posixpath.dirname(d)
                if p.startswith(abs_top):
                    ensure_dir(p)
                    tree[p][0].add(posixpath.basename(d))
                    ensure_dir(d)
        # Ensure the top-level directory is in the tree for virtual-only directories
        if abs_top not in tree and abs_top in self.folders:
            ensure_dir(abs_top)

        # 3. Yield merged tree
        visited = set()
        def _walk(curr):
            if curr in visited: return
            visited.add(curr)
            if curr in tree:
                ds, fs = tree[curr]
                d_list = sorted(list(ds))
                yield curr, d_list, sorted(list(fs))
                for d in d_list:
                    yield from _walk(posixpath.join(curr, d))

        yield from _walk(abs_top)