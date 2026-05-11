import os
import sys
import shlex
import shutil
import subprocess
import psutil
from PySide6.QtWidgets import QMessageBox
from systems.os.platform import is_windows, get_venv_python_path, open_file_externally
from .scripts import ScriptManager

class ProjectExecutor:
    def __init__(self, app):
        self.app = app

    def _build_command(self, launch_file, args_text):
        root_path = self.app.root_path

        if launch_file.endswith('.py'):
            venv_py = get_venv_python_path(root_path)
            if os.path.exists(venv_py):
                if is_windows():
                    base_cmd = f'& "{venv_py}" "{launch_file}"'
                else:
                    base_cmd = f'"{venv_py}" "{launch_file}"'
            else:
                base_cmd = f'python "{launch_file}"' if is_windows() else f'python3 "{launch_file}"'

        elif launch_file.endswith(('.bat', '.cmd')):
            if is_windows():
                if args_text:
                    return f"cmd /c '\"\"{launch_file}\" {args_text}\"'"
                else:
                    return f"cmd /c '\"\"{launch_file}\"\"'"
            else:
                base_cmd = f'sh "{launch_file}"'

        elif launch_file.endswith('.sh'):
            base_cmd = f'bash "{launch_file}"'

        elif launch_file.endswith(('.ps1', '.exe')):
            if is_windows():
                base_cmd = f'& ".\\{launch_file}"'
            else:
                base_cmd = f'"./{launch_file}"'

        elif launch_file.endswith('.html'):
            if is_windows():
                base_cmd = f'Start-Process "{launch_file}"'
            else:
                base_cmd = f'echo "Please open {launch_file} manually"'

        elif launch_file.endswith('.js'):
            base_cmd = f'node "{launch_file}"'

        elif launch_file.endswith('.ts'):
            base_cmd = f'ts-node "{launch_file}"'

        else:
            if is_windows():
                base_cmd = f'& ".\\{launch_file}"'
            else:
                base_cmd = f'"./{launch_file}"'

        if args_text:
            return f"{base_cmd} {args_text}"
        return base_cmd

    def start_internal(self, launch_file, args_text):
        full_path = os.path.join(self.app.root_path, launch_file)
        
        if launch_file.endswith('.html'):
            open_file_externally(full_path)
            return

        if args_text:
            ScriptManager.ensure_args_support(full_path)

        final_command = self._build_command(launch_file, args_text)

        if hasattr(self.app.widget, 'console'):
            if not self.app.widget.console.is_running():
                self.app.widget.console.start_session()
            self.app.widget.console.send_external_command(final_command)

        self.app.launch_mode = 'internal'
        self.app.widget._update_ui_state()

    def start_external(self, launch_file, args_text):
        full_path = os.path.join(self.app.root_path, launch_file)
        if launch_file.endswith('.html'):
            open_file_externally(full_path)
            return
        
        if args_text:
            ScriptManager.ensure_args_support(full_path)

        if launch_file.endswith('.py'):
            venv_py = get_venv_python_path(self.app.root_path)
            py_exe = venv_py if os.path.exists(venv_py) else ("python" if is_windows() else "python3")
            base_cmd = f'"{py_exe}" "{full_path}"'
        elif launch_file.endswith('.js'):
            base_cmd = f'node "{full_path}"'
        elif launch_file.endswith('.sh'):
            base_cmd = f'bash "{full_path}"'
        else:
            base_cmd = f'"{full_path}"'

        if args_text:
            safe_cmd = f'{base_cmd} {args_text}'
        else:
            safe_cmd = base_cmd

        try:
            if is_windows():
                creation_flags = subprocess.CREATE_NEW_CONSOLE
                command_line = f'cmd /k "{safe_cmd}"'

                self.app.external_process = subprocess.Popen(
                    command_line,
                    cwd=self.app.root_path,
                    creationflags=creation_flags,
                    shell=False
                )
            else:
                if sys.platform == 'darwin':
                    self._launch_macos(safe_cmd)
                else:
                    import tempfile
                    script_content = f"#!/bin/bash\ncd {shlex.quote(self.app.root_path)}\n{safe_cmd}\nread -p 'Press Enter to close...' "
                    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.sh', dir=self.app.root_path, encoding='utf-8') as f:
                        f.write(script_content)
                        os.chmod(f.name, 0o755)
                        temp_file_name = f.name

                    terminals = [
                        ['x-terminal-emulator', '-e', temp_file_name],
                        ['gnome-terminal', '--', temp_file_name],['konsole', '-e', temp_file_name],
                        ['xfce4-terminal', '-e', temp_file_name],
                        ['xterm', '-e', temp_file_name]
                    ]

                    launched = False
                    for term_cmd in terminals:
                        if shutil.which(term_cmd[0]):
                            subprocess.Popen(term_cmd, cwd=self.app.root_path)
                            launched = True
                            break

                    if not launched:
                        raise FileNotFoundError("No supported terminal emulator found (tried gnome-terminal, konsole, xfce4-terminal, xterm).")
    
            self.app.launch_mode = 'external'
            self.app.widget._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self.app.widget, self.app.lang.get('patch_load_error_title'), f"Failed to launch external: {e}")

    def _launch_macos(self, safe_cmd):
        import tempfile
        script_content = f"#!/bin/bash\ncd {shlex.quote(self.app.root_path)}\n{safe_cmd}\nread -p 'Press Enter to close...' "
    
        temp_file_name = ""
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.command', dir=self.app.root_path, encoding='utf-8') as f:
            f.write(script_content)
            os.chmod(f.name, 0o755)
            temp_file_name = f.name
    
        if temp_file_name:
            subprocess.call(['open', temp_file_name])

    def stop(self):
        # 1. Handle External Process
        if self.app.launch_mode == 'external' and self.app.external_process:
            try:
                parent = psutil.Process(self.app.external_process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except (psutil.NoSuchProcess, Exception):
                pass
            self.app.external_process = None
            self.app.launch_mode = None
            self.app.widget._update_ui_state()
            return
    
        # 2. Handle Internal Process
        if hasattr(self.app.widget, 'console') and self.app.widget.console.is_running():
            self.app.widget.console.restart_session()
            self.app.launch_mode = None
            self.app.widget._update_ui_state()