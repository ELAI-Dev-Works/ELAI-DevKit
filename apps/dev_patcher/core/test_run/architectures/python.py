import os
from systems.os.platform import is_windows, get_venv_python_path
from .base import BaseArchitecture

class PythonArchitecture(BaseArchitecture):
    def get_launch_command(self, is_trusted=False):
        venv_py = get_venv_python_path(self.project_root)
        py_exe = venv_py if os.path.exists(venv_py) else ("python" if is_windows() else "python3")

        cmd_list = [py_exe, self.launch_file]
        cmd_list = self._apply_sandbox(cmd_list, is_trusted)

        if is_windows():
            cmd_str = " ".join(f'"{c}"' for c in cmd_list)
            return f"& {cmd_str}"
        else:
            import shlex
            return " ".join(shlex.quote(c) for c in cmd_list)