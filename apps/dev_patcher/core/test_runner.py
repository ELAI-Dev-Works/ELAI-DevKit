import os
import subprocess
import tempfile
import shutil
from typing import List, Tuple, Generator

class TestRunner:
    """
    Manages the test run of a patched project in an isolated environment.
    """
    def __init__(self, vfs, project_root: str, launch_file: str):
        self.vfs = vfs
        self.project_root = project_root
        self.launch_file = launch_file # Changed from 'command'
        self.temp_dir = None

    def _prepare_environment(self) -> None:
        """
        Creates a temporary directory and populates it with modified files from the VFS.
        """
        self.temp_dir = tempfile.mkdtemp(prefix="patcher_test_run_")

        # We only write files that have been modified or created in the VFS.
        # The VFS tracks original files with a special marker, which we can use to differentiate.
        from .fs_handler import _LAZY_LOAD_MARKER

        for file_path, content in self.vfs.files.items():
            if content is not _LAZY_LOAD_MARKER:
                # This file was changed. Recreate its structure in the temp dir.
                relative_path = os.path.relpath(file_path, self.vfs.root)
                temp_file_path = os.path.join(self.temp_dir, relative_path)
                os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

                if isinstance(content, bytes):
                    with open(temp_file_path, 'wb') as f:
                        f.write(content)
                else:
                    with open(temp_file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

    def _cleanup_environment(self) -> None:
        """
        Removes the temporary directory.
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def run(self) -> Generator[str, None, None]:
        """
        Executes the test run and yields stdout/stderr lines.
        """
        try:
            self._prepare_environment()
            yield f"[INFO] Temporary directory for patched files: {self.temp_dir}"

            ext = os.path.splitext(self.launch_file)[1].lower()

            # --- HTML LAUNCH ---
            if ext == '.html':
                # Reconstruct the full path inside the temp directory
                # os.path.join doesn't work well with @ROOT, so we use relpath
                relative_path_from_vfs_root = os.path.relpath(os.path.join(self.vfs.root, self.launch_file), self.vfs.root)
                full_temp_path = os.path.join(self.temp_dir, relative_path_from_vfs_root)

                yield f"[INFO] Opening HTML file: {full_temp_path}"
                os.startfile(full_temp_path)
                yield "="*40
                yield "[INFO] HTML file opened in default browser."
                return

            # --- CONSOLE LAUNCH (PY, BAT, EXE etc) ---
            command = []
            # CRITICAL FIX: The working directory MUST be the project root for all commands.
            cwd = self.project_root
            env = os.environ.copy()
            
            # Create an "overlay" by prepending the temp directory to the system's PATH.
            # This makes the OS look for executables in our temp folder first.
            env['PATH'] = os.pathsep.join([self.temp_dir, env.get('PATH', '')])
            
            if ext == '.py':
                venv_path = os.path.join(self.project_root, '.venv')
                python_exe = os.path.join(venv_path, 'Scripts', 'python.exe') if os.path.isdir(venv_path) else 'python'
                command = [python_exe, self.launch_file]
            
                # Also create a PYTHONPATH overlay for Python imports.
                python_path = [self.temp_dir, self.project_root]
                if 'PYTHONPATH' in env:
                    python_path.extend(env['PYTHONPATH'].split(os.pathsep))
                env['PYTHONPATH'] = os.pathsep.join(python_path)
                yield f"[INFO] PYTHONPATH: {env['PYTHONPATH']}"
            
            elif ext in ['.bat', '.cmd']:
                # The command is simply the file name; the modified PATH and CWD will handle resolution.
                command = ['cmd', '/c', self.launch_file]
            
            else: # .exe and others
                # The command is the file name; the modified PATH and CWD will find it.
                command = [self.launch_file]

            yield f"[INFO] Running command: {' '.join(command)}"
            yield f"[INFO] CWD: {cwd}"
            yield "="*40

            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW # Hide console window on Windows
            )

            for line in iter(process.stdout.readline, ''):
                yield line.strip()

            process.stdout.close()
            return_code = process.wait()
            yield "="*40
            yield f"[INFO] The process exited with code: {return_code}"

        except Exception as e:
            import traceback
            yield f"\n[ERROR] Critical error during test run: {e}"
            yield traceback.format_exc()
        finally:
            self._cleanup_environment()