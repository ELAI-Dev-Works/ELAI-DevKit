import os
from .python import PythonArchitecture
from .nodejs import NodeJSArchitecture
from .web import WebArchitecture

def get_architecture(temp_dir, project_root, launch_file):
    ext = os.path.splitext(launch_file)[1].lower()
    
    if ext == '.py':
        return PythonArchitecture(temp_dir, project_root, launch_file)
    elif ext in ['.js', '.ts']:
        return NodeJSArchitecture(temp_dir, project_root, launch_file)
    elif ext in ['.html', '.htm']:
        return WebArchitecture(temp_dir, project_root, launch_file)
    else:
        # Generic fallback for bat, sh, cmd, exe
        from .base import BaseArchitecture
        class GenericArchitecture(BaseArchitecture):
            def get_launch_command(self):
                from systems.os.platform import is_windows
                if is_windows():
                    return f"& \".\\{self.launch_file}\""
                else:
                    if self.launch_file.lower().endswith('.sh'):
                        return f"bash \"{self.launch_file}\""
                    return f"\"./{self.launch_file}\""
        return GenericArchitecture(temp_dir, project_root, launch_file)