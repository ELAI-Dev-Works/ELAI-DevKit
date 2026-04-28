import os
from systems.os.platform import is_windows, get_venv_python_path
from .base import BaseArchitecture

class PythonArchitecture(BaseArchitecture):
    def get_launch_command(self):
        venv_py = get_venv_python_path(self.project_root)
        py_exe = venv_py if os.path.exists(venv_py) else ("python" if is_windows() else "python3")

        if is_windows():
            return f"& \"{py_exe}\" \"{self.launch_file}\""
        else:
            return f"\"{py_exe}\" \"{self.launch_file}\""