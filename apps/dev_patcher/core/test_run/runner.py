import os
import tempfile
import shutil

class TestRunner:
    """
    Orchestrates the sandbox environment for a test run.
    """
    def __init__(self, vfs, project_root):
        self.vfs = vfs
        self.project_root = project_root
        self.temp_dir = None

    def prepare(self) -> str:
        """
        Creates a temporary directory and populates it with modified files from the VFS.
        Uses Hardlinks and Junctions/Symlinks to mirror the rest of the project efficiently.
        """
        self.temp_dir = tempfile.mkdtemp(prefix="patcher_test_run_")
        from apps.dev_patcher.core.fs_handler import _LAZY_LOAD_MARKER
        from systems.os.platform import is_windows
        import subprocess

        heavy_dirs = {'.venv', 'node_modules', '.git', '__pycache__', '.idea', 'build', 'dist'}

        modified_files = {}
        for file_path, content in self.vfs.files.items():
            if content is not _LAZY_LOAD_MARKER:
                rel_path = os.path.relpath(file_path, self.vfs.root).replace('\\', '/')
                modified_files[rel_path] = content

        for root, dirs, files in os.walk(self.project_root):
            rel_root = os.path.relpath(root, self.project_root)
            if rel_root == '.':
                rel_root = ''

            dirs_to_remove =[]
            for d in dirs:
                if d in heavy_dirs:
                    rel_d = os.path.join(rel_root, d).replace('\\', '/').strip('/')
                    src_dir = os.path.join(root, d)
                    dst_dir = os.path.join(self.temp_dir, rel_d)
                    os.makedirs(os.path.dirname(dst_dir), exist_ok=True)
                    if not os.path.exists(dst_dir):
                        if is_windows():
                            subprocess.run(['cmd', '/c', 'mklink', '/J', f'"{dst_dir}"', f'"{src_dir}"'], capture_output=True)
                        else:
                            os.symlink(src_dir, dst_dir, target_is_directory=True)
                    dirs_to_remove.append(d)

            for d in dirs_to_remove:
                dirs.remove(d)

            target_dir = os.path.join(self.temp_dir, rel_root)
            os.makedirs(target_dir, exist_ok=True)

            for f in files:
                rel_f = os.path.join(rel_root, f).replace('\\', '/').strip('/')
                src_file = os.path.join(root, f)
                dst_file = os.path.join(self.temp_dir, rel_root, f)

                if rel_f in modified_files:
                    content = modified_files.pop(rel_f)
                    if isinstance(content, bytes):
                        with open(dst_file, 'wb') as f_out:
                            f_out.write(content)
                    else:
                        with open(dst_file, 'w', encoding='utf-8') as f_out:
                            f_out.write(content)
                else:
                    try:
                        os.link(src_file, dst_file)
                    except OSError:
                        shutil.copy2(src_file, dst_file)

        for rel_path, content in modified_files.items():
            dst_file = os.path.join(self.temp_dir, os.path.normpath(rel_path))
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            if isinstance(content, bytes):
                with open(dst_file, 'wb') as f_out:
                    f_out.write(content)
            else:
                with open(dst_file, 'w', encoding='utf-8') as f_out:
                    f_out.write(content)

        return self.temp_dir

    def cleanup(self) -> None:
        """
        Removes the temporary directory.
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)