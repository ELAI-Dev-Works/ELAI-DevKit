import os
import shutil
import tempfile
from typing import Generator
from systems.os.platform import get_venv_python_path

from .code.python import check_python
from .code.javascript_typescript import check_js_ts
from .code.html_css import check_html_css
from .code.json_check import check_json
from .code.xml_check import check_xml

class CodeChecker:
    def __init__(self, vfs, project_root: str):
        self.vfs = vfs
        self.project_root = project_root
        self.temp_dir = None
        self.errors = []

    def _prepare_environment(self) -> None:
        import uuid
        temp_project_dir = os.path.join(self.project_root, '.temp_project')
        os.makedirs(temp_project_dir, exist_ok=True)
        self.temp_dir = os.path.join(temp_project_dir, f"code_check_{uuid.uuid4().hex[:8]}")
        os.makedirs(self.temp_dir, exist_ok=True)

        for file_path in self.vfs.modified_paths:
            if self.vfs.exists(file_path) and not self.vfs.is_dir(file_path):
                content = self.vfs.read_bytes(file_path)
                relative_path = os.path.relpath(file_path, self.vfs.root)
                temp_file_path = os.path.join(self.temp_dir, relative_path)
                os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                with open(temp_file_path, 'wb') as f:
                    f.write(content)

    def _cleanup_environment(self) -> None:
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run(self) -> Generator[str, None, None]:
        self.errors = []
        try:
            self._prepare_environment()
            yield f"[INFO] Temporary directory for code check: {self.temp_dir}"

            python_exe = get_venv_python_path(self.project_root)
            if not os.path.exists(python_exe):
                python_exe = "python" if os.name == 'nt' else "python3"

            has_node = shutil.which("node") is not None
            checked_files = 0

            for file_path in self.vfs.modified_paths:
                if not self.vfs.exists(file_path) or self.vfs.is_dir(file_path):
                    continue

                content = self.vfs.read_bytes(file_path)
                relative_path = os.path.relpath(file_path, self.vfs.root)
                temp_file_path = os.path.join(self.temp_dir, relative_path)
                ext = os.path.splitext(relative_path)[1].lower()

                # Convert to string for passing to formatters
                content_str = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else content

                error = None
                if ext == '.py':
                    yield f"  Checking {relative_path} (Python)..."
                    checked_files += 1
                    error = check_python(temp_file_path, content_str, python_exe)
                elif ext in ['.js', '.ts'] and has_node:
                    yield f"  Checking {relative_path} (NodeJS)..."
                    checked_files += 1
                    error = check_js_ts(temp_file_path, content_str)
                elif ext == '.json':
                    yield f"  Checking {relative_path} (JSON)..."
                    checked_files += 1
                    error = check_json(content_str)
                elif ext == '.xml':
                    yield f"  Checking {relative_path} (XML)..."
                    checked_files += 1
                    error = check_xml(content_str)
                elif ext in ['.html', '.htm', '.css']:
                    lang_name = 'html' if ext.startswith('.htm') else 'css'
                    yield f"  Checking {relative_path} ({lang_name.upper()})..."
                    checked_files += 1
                    error = check_html_css(content_str, lang_name)

                if error:
                    self.errors.append((relative_path, error))

            if checked_files == 0:
                yield "[INFO] No modified Python, JS, TS, HTML, CSS, JSON or XML files to check."

        except Exception as e:
            import traceback
            yield f"[ERROR] Code check process failed: {e}"
            self.errors.append(("System", traceback.format_exc()))
        finally:
            self._cleanup_environment()