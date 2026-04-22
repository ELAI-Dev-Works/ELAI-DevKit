import os
import shutil
import posixpath
from typing import Dict, Union
from systems.project.ignore_handler import IgnoreHandler
# Ensure os is imported

class BaseFileSystem:
    def __init__(self, root_path: str):
        # Normalize the root path on initialization for consistency
        self.root = os.path.abspath(root_path).replace('\\', '/')

    def _to_abs(self, path):
        # Security: strictly forbid absolute paths in input to prevent bypassing @ROOT logic
        # Check both POSIX / and Windows C: styles
        if os.path.isabs(path) or (os.name == 'nt' and ':' in path):
            # Allow absolute paths if they are inside the project root (needed for internal tools like REFACTOR)
            norm_path = os.path.normpath(path)
            norm_root = os.path.normpath(self.root)
    
            check_path = norm_path.lower() if os.name == 'nt' else norm_path
            check_root = norm_root.lower() if os.name == 'nt' else norm_root
    
            if check_path == check_root or check_path.startswith(check_root + os.sep):
                return path.replace('\\', '/')
    
            raise ValueError(f"Security Violation: Absolute paths are not allowed in patches. Use '@ROOT' or relative paths. Invalid path: '{path}'")
    
        # Resolve path relative to self.root
        if path.startswith('@ROOT'):
            path_part = path.replace('@ROOT', '', 1).lstrip('/')
            # Use posixpath to join to ensure forward slashes are respected if mixed
            full_path = posixpath.join(self.root, path_part)
        elif path.startswith('./'):
            full_path = posixpath.join(self.root, path[2:])
        elif path.startswith('@APP-ROOT'):
            path_part = path.replace('@APP-ROOT', '', 1).lstrip('/')
            full_path = posixpath.join(self.root, path_part)
        else:
            full_path = posixpath.join(self.root, path)
    
        # Normalize to resolve '..' and check boundaries
        # We must use os.path.normpath to correctly handle system separators when checking bounds
        norm_full_path = os.path.normpath(full_path)
        norm_root = os.path.normpath(self.root)
    
        # Prepare for case-insensitive comparison on Windows
        check_path = norm_full_path.lower() if os.name == 'nt' else norm_full_path
        check_root = norm_root.lower() if os.name == 'nt' else norm_root
    
        # Sandbox Check: Ensure the path starts with the root
        # We append a separator to root to ensure /root1 doesn't match /root
        # Exception: if the path is exactly the root itself
        if check_path != check_root and not check_path.startswith(check_root + os.sep):
             raise PermissionError(f"Security Violation: Path resolves outside the project root.\nTarget: {full_path}\nRoot: {self.root}")
    
        return full_path.replace('\\', '/')

# Special marker to indicate "lazy" loading
_LAZY_LOAD_MARKER = object()

class VirtualFileSystem(BaseFileSystem):
    def __init__(self, root_path: str, ignore_dirs: list = None, ignore_context: str = None):
        super().__init__(root_path)
        # The self.files dictionary now stores either content or a lazy load marker
        self.files: Dict[str, Union[str, bytes, object]] = {}
        self.folders: set = {self.root}

        # Default ignores are now handled by the handler
        final_ignore_dirs = ignore_dirs if ignore_dirs is not None else[]
        if '.git' not in final_ignore_dirs:
            final_ignore_dirs.append('.git')

        self.ignore_handler = IgnoreHandler(final_ignore_dirs,[], context=ignore_context)
        self._index_real_fs()

    def _index_real_fs(self):
        """
        Indexes the real FS: creates a list of files and folders, but does not read their content.
        A special marker is placed instead of the content for existing files.
        """
        for dirpath, dirnames, filenames in os.walk(self.root):
            # Exclude folders from further traversal using the provided list
            dirnames[:] = [d for d in dirnames if not self.ignore_handler.is_ignored(d, is_dir=True)]

            dirpath_posix = dirpath.replace('\\', '/')
            for d in dirnames:
                self.folders.add(posixpath.join(dirpath_posix, d))
            for f in filenames:
                file_path_posix = posixpath.join(dirpath_posix, f)
                # Mark the file for lazy loading
                self.files[file_path_posix] = _LAZY_LOAD_MARKER

    def _load_file_content(self, abs_path: str) -> Union[str, bytes]:
        """
        Actually loads the file content from the disk. Called only when necessary.
        """
        binary_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.tif', '.tiff',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.exe', '.dll', '.so', '.a', '.lib',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.mp3', '.wav', '.ogg', '.mp4', '.avi', '.mov', '.mkv',
            '.db', '.sqlite', '.sqlite3',
            '.pyc', '.pyd'
        }
        content = b"[read error]"  # Default value in case of an error
        try:
            _, ext = posixpath.splitext(abs_path)
            if ext.lower() in binary_extensions:
                with open(abs_path, 'rb') as file:
                    content = file.read()
            else:
                try:
                    with open(abs_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                except UnicodeDecodeError:
                    # Retry in binary mode if UTF-8 failed
                    with open(abs_path, 'rb') as file:
                        content = file.read()
        except (IOError, OSError):
            # Leave content as b"[read error]"
            pass
        
        # Cache the result (even if it's a read error)
        self.files[abs_path] = content
        return content

    def exists(self, path):
        abs_path = self._to_abs(path)
        return abs_path in self.files or abs_path in self.folders

    def is_dir(self, path):
        return self._to_abs(path) in self.folders

    def read(self, path):
        abs_path = self._to_abs(path)
        if not self.exists(path) or self.is_dir(path):
            raise FileNotFoundError(f"File not found or is a folder: {abs_path}")

        content = self.files.get(abs_path)
        
        # If the content is not yet loaded, load it
        if content is _LAZY_LOAD_MARKER:
            content = self._load_file_content(abs_path)

        return content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content

    def read_bytes(self, path):
        abs_path = self._to_abs(path)
        if not self.exists(path) or self.is_dir(path):
            raise FileNotFoundError(f"File not found or is a folder: {abs_path}")

        content = self.files.get(abs_path)

        # If the content is not yet loaded, load it
        if content is _LAZY_LOAD_MARKER:
            content = self._load_file_content(abs_path)

        return content if isinstance(content, bytes) else content.encode('utf-8')
    
    def _add_abs_path_to_folders(self, abs_path):
        """Internal helper to add absolute directory path to virtual folders recursively."""
        if abs_path in self.folders:
            return
        temp_path = abs_path
        while temp_path and temp_path != self.root and temp_path not in self.folders:
            self.folders.add(temp_path)
            parent = posixpath.dirname(temp_path)
            if parent == temp_path: break
            temp_path = parent
    

    def write(self, path, content: str):
        if isinstance(content, bytes):
            raise TypeError("The write method expects a string (str), but received bytes (bytes). Use write_bytes.")
        abs_path = self._to_abs(path)
        parent_dir = posixpath.dirname(abs_path)
        if parent_dir:
            self._add_abs_path_to_folders(parent_dir)
        self.files[abs_path] = content
    
    def write_bytes(self, path, content: bytes):
        abs_path = self._to_abs(path)
        parent_dir = posixpath.dirname(abs_path)
        if parent_dir:
            self._add_abs_path_to_folders(parent_dir)
        self.files[abs_path] = content
    
    def makedirs(self, path):
        abs_path = self._to_abs(path)
        target_dir = posixpath.dirname(abs_path) if posixpath.splitext(abs_path)[1] else abs_path
        self._add_abs_path_to_folders(target_dir)

    def _recursive_op(self, src, dst, op_type):
        abs_src, abs_dst = self._to_abs(src), self._to_abs(dst)
        if not self.exists(src): raise FileNotFoundError(f"Source not found: {abs_src}")
    
        if self.is_dir(src):
            # Move/Copy Directory Content
            for path, content in list(self.files.items()):
                if path.startswith(abs_src + '/'):
                    if content is _LAZY_LOAD_MARKER:
                        content = self._load_file_content(path)
                    new_path = path.replace(abs_src, abs_dst, 1)
                    self.files[new_path] = content
                    if op_type == 'move': del self.files[path]
    
            for path in list(self.folders):
                if path.startswith(abs_src + '/'):
                    new_path = path.replace(abs_src, abs_dst, 1)
                    self.folders.add(new_path)
                    if op_type == 'move': self.folders.remove(path)
    
            # Handle root folder
            self.folders.add(abs_dst)
            if op_type == 'move':
                if abs_src in self.folders: self.folders.remove(abs_src)
        else:
            # Move/Copy Single File
            final_dst = abs_dst
            if self.is_dir(dst):
                final_dst = posixpath.join(self._to_abs(dst), posixpath.basename(abs_src))
    
            content = self.files.get(abs_src)
            if content is _LAZY_LOAD_MARKER:
                content = self._load_file_content(abs_src)
    
            self.files[final_dst] = content
            if op_type == 'move':
                del self.files[abs_src]

    def move(self, src, dst): self._recursive_op(src, dst, 'move')
    def copy(self, src, dst): self._recursive_op(src, dst, 'copy')
    def rename(self, src, dst): self.move(src, dst)

    def delete(self, path):
        abs_path = self._to_abs(path)
        if not self.exists(path): return

        if self.is_dir(path):
            # Delete all nested files and folders
            for p in list(self.files.keys()):
                if p.startswith(abs_path + '/'): del self.files[p]
            for p in list(self.folders):
                if p.startswith(abs_path + '/'): self.folders.remove(p)
            self.folders.remove(abs_path)
        else:
            if abs_path in self.files: del self.files[abs_path]

    def walk(self, top):
        abs_top = self._to_abs(top)
        # Pre-build the entire directory structure map from the VFS cache
        dir_map = {d: ([], []) for d in self.folders}
        for p in self.files.keys():
            parent = posixpath.dirname(p)
            if parent in dir_map:
                dir_map[parent][1].append(posixpath.basename(p))
        for d in self.folders:
            parent = posixpath.dirname(d)
            if parent in dir_map and parent != d:
                dir_map[parent][0].append(posixpath.basename(d))

        # Now, emulate os.walk respecting in-place modification of dirnames
        paths_to_visit = [abs_top]
        while paths_to_visit:
            current_path = paths_to_visit.pop(0)

            # Get the contents for the current path
            if current_path in dir_map:
                dirs, files = dir_map[current_path]
                # Sort them to ensure consistent order
                dirs.sort()
                files.sort()

                # Yield to the caller, who can now modify `dirs` in-place
                yield current_path, dirs, files

                # The caller might have removed items from `dirs`.
                # We continue the traversal with the modified list.
                for d_name in dirs:
                    paths_to_visit.append(posixpath.join(current_path, d_name))

    def clone(self):
        """
        Creates and returns a clone of the current virtual file system.
        Used to create isolated states in simulations.
        """
        # __init__ is not called to avoid re-indexing the disk
        new_vfs = self.__class__.__new__(self.__class__)
        new_vfs.root = self.root
        # Create shallow copies of the dictionary and set.
        # This is fast and safe, as strings/bytes are immutable,
        # and the marker is a singleton.
        new_vfs.files = self.files.copy()
        new_vfs.folders = self.folders.copy()
        return new_vfs
                        
class RealFileSystem(BaseFileSystem):
    def exists(self, path): return os.path.exists(self._to_abs(path))
    def is_dir(self, path): return os.path.isdir(self._to_abs(path))
    def read(self, path):
        with open(self._to_abs(path), 'r', encoding='utf-8', errors='ignore') as f: return f.read()
    
    def read_bytes(self, path):
        with open(self._to_abs(path), 'rb') as f: return f.read()

    def write(self, path, content: str):
        if isinstance(content, bytes):
            raise TypeError("The write method expects a string (str), but received bytes (bytes). Use write_bytes.")
        abs_path = self._to_abs(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f: f.write(content)

    def write_bytes(self, path, content: bytes):
        abs_path = self._to_abs(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'wb') as f: f.write(content)
    def makedirs(self, path): os.makedirs(self._to_abs(path), exist_ok=True)
    def move(self, src, dst): shutil.move(self._to_abs(src), self._to_abs(dst))
    def copy(self, src, dst):
        abs_src, abs_dst = self._to_abs(src), self._to_abs(dst)
        if self.is_dir(src): shutil.copytree(abs_src, abs_dst, dirs_exist_ok=True)
        else: shutil.copy2(abs_src, abs_dst)
    def rename(self, src, dst): os.rename(self._to_abs(src), self._to_abs(dst))
    def delete(self, path):
        abs_path = self._to_abs(path)
        if self.is_dir(path): shutil.rmtree(abs_path)
        elif os.path.exists(abs_path): os.remove(abs_path)
    def walk(self, top): return os.walk(self._to_abs(top))