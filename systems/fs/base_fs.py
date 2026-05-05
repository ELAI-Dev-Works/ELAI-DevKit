import os
import posixpath

class BaseFileSystem:
    def __init__(self, root_path: str):
        self.memory = None
        self.root = os.path.abspath(root_path).replace('\\', '/')

    def _to_abs(self, path: str) -> str:
        if os.path.isabs(path) or (os.name == 'nt' and ':' in path):
            norm_path = os.path.normpath(path)
            norm_root = os.path.normpath(self.root)
            check_path = norm_path.lower() if os.name == 'nt' else norm_path
            check_root = norm_root.lower() if os.name == 'nt' else norm_root
            if check_path == check_root or check_path.startswith(check_root + os.sep):
                return path.replace('\\', '/')
            raise ValueError(f"Security Violation: Absolute paths are not allowed. Invalid path: '{path}'")

        if path.startswith('@ROOT'):
            path_part = path.replace('@ROOT', '', 1).lstrip('/\\')
            full_path = posixpath.join(self.root, path_part)
        elif path.startswith('./'):
            full_path = posixpath.join(self.root, path[2:])
        elif path.startswith('@APP-ROOT'):
            path_part = path.replace('@APP-ROOT', '', 1).lstrip('/\\')
            full_path = posixpath.join(self.root, path_part)
        else:
            full_path = posixpath.join(self.root, path)

        norm_full_path = os.path.normpath(full_path)
        norm_root = os.path.normpath(self.root)
        check_path = norm_full_path.lower() if os.name == 'nt' else norm_full_path
        check_root = norm_root.lower() if os.name == 'nt' else norm_root

        if check_path != check_root and not check_path.startswith(check_root + os.sep):
             raise PermissionError(f"Security Violation: Path resolves outside the root.\nTarget: {full_path}\nRoot: {self.root}")

        return full_path.replace('\\', '/')