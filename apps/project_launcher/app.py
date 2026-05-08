import os
import subprocess
import sys
import psutil
import shlex
import shutil
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox
from systems.os.platform import is_windows, open_file_externally, get_venv_python_path


class ProjectLauncherApp(QObject):
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.lang = context.lang
        self.settings_manager = context.settings_manager
        self.widget = None

        self.root_path = None
        if hasattr(self.context, 'main_window') and self.context.main_window:
             self.root_path = self.context.main_window.root_path
        self.selected_launch_file = {}
        self.selected_launch_args = {}
        
        # State tracking
        self.launch_mode = None # 'internal', 'external', or None
        self.external_process = None

    def set_widget(self, widget):
        self.widget = widget

    def project_folder_changed(self, root_path):
        self.stop_project()
        self.root_path = root_path
        self.widget.launch_file_combo.clear()

        if self.root_path:
            self.widget.status_label_text.setText(self.lang.get('pl_status_scanning'))
            self.widget.start_button.setEnabled(False)

            fs = self.context.fs.get_fs(self.root_path)

            def scan_task():
                launch_files = {'run_bat': None, 'other_bats': [], 'scripts':[]}
                input_requirements = {}
                has_requirements = False
                should_suggest = False

                if not fs.root or not fs.exists(""):
                    return launch_files, input_requirements, False

                for item in fs.listdir(""):
                    if not fs.exists(item) or fs.is_dir(item): continue

                    lower_item = item.lower()
                    needs_input = False

                    # Always allow input for executable scripts to avoid user confusion
                    # regarding arguments or standard input availability.
                    if lower_item.endswith(('.py', '.js', '.ts', '.bat', '.ps1', '.cmd', '.c', '.cpp', '.h', '.sh', '.exe')):
                        needs_input = True

                    input_requirements[item] = needs_input

                    if lower_item == 'run.bat' and is_windows():
                        launch_files['run_bat'] = item
                    elif lower_item == 'run.sh' and not is_windows():
                        launch_files['run_bat'] = item
                    elif lower_item.endswith('.bat'):
                        launch_files['other_bats'].append(item)
                    elif lower_item.endswith(('.py', '.html', '.exe', '.js', '.ts', '.sh')):
                        launch_files['scripts'].append(item)
                    elif lower_item in ('requirements.txt', 'requirements.in', 'package.json'):
                        has_requirements = True

                if not launch_files['run_bat'] and not launch_files['other_bats'] and has_requirements:
                    should_suggest = True

                return launch_files, input_requirements, should_suggest

            def on_scanned(result):
                launch_files, input_reqs, should_suggest = result
                self.widget._on_scan_finished(launch_files, input_reqs)
                if should_suggest:
                    self.widget._on_creation_suggestion()

            tc = self.context.async_thread_manager.thread
            tc.run_in_background(
                scan_task,
                callback=on_scanned,
                error_callback=lambda e: self.widget._on_scan_error(str(e)),
                use_qt=True
            )
        else:
            self.widget._update_ui_state()

    def create_run_bat(self):
        fs = self.context.fs.get_fs(self.root_path)
        if is_windows():
            filename = "run.bat"
            content = "@echo off\nsetlocal\necho [ELAI] Auto-generated run.bat\n"
            if fs.exists('package.json'):
                 content += "echo Installing dependencies...\ncall npm install\necho Starting...\nnpm start\n"
            else:
                 content += "echo Preparing environment...\npython -m venv .venv\n.\\.venv\\Scripts\\pip.exe install -r requirements.txt\n.\\.venv\\Scripts\\python.exe main.py\n"
            content += "pause\n"
        else:
            filename = "run.sh"
            content = "#!/bin/bash\n\n"
            if fs.exists('package.json'):
                 content += "echo 'Installing dependencies...'\nnpm install\necho 'Starting...'\nnpm start\n"
            else:
                 content += "echo 'Preparing environment...'\npython3 -m venv .venv\n./.venv/bin/pip install -r requirements.txt\n./.venv/bin/python main.py\n"
            content += "read -p 'Press Enter to exit...' arg\n"

        try:
            if filename.endswith('.sh'):
                fs.write_bytes(filename, content.replace('\r\n', '\n').encode('utf-8'))
            else:
                fs.write(filename, content)

            if not is_windows():
                os.chmod(fs._to_abs(filename), 0o755)

            QMessageBox.information(self.widget, self.lang.get('pl_status_done'), self.lang.get('pl_run_bat_created_msg').format(filename))
            self.project_folder_changed(self.root_path)
        except Exception as e:
            QMessageBox.critical(self.widget, self.lang.get('patch_load_error_title'), str(e))

    def open_project_folder(self):
        if self.root_path and os.path.isdir(self.root_path):
            try:
                open_file_externally(self.root_path)
            except Exception as e:
                QMessageBox.critical(self.widget, self.lang.get('patch_load_error_title'), f"Failed to open folder: {e}")

    def open_in_vscode(self):
        if self.root_path and os.path.isdir(self.root_path):
            try:
                # Redirect streams to DEVNULL to prevent Electron/ICU errors (Invalid file descriptor)
                subprocess.Popen(
                    'code .',
                    cwd=self.root_path,
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                QMessageBox.critical(self.widget, self.lang.get('patch_load_error_title'), f"Failed to open in VS Code: {e}")

    def _ensure_args_support(self, full_path):
        """Automatically appends %* or $@ to script files if they lack argument support."""
        if not os.path.exists(full_path): return
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return

        modified = False
        lines = content.splitlines()

        if full_path.lower().endswith(('.bat', '.cmd')):
            if '%*' not in content:
                last_exec_idx = -1
                for i, line in enumerate(lines):
                    stripped = line.strip().lower()
                    if ('python' in stripped or 'node' in stripped or 'uv run' in stripped or 'pytest' in stripped) \
                       and not stripped.startswith(('echo', 'rem', 'set', 'if', 'goto', 'call')) \
                       and ' venv ' not in stripped and ' pip ' not in stripped and ' npm ' not in stripped:
                        last_exec_idx = i
                if last_exec_idx != -1:
                    lines[last_exec_idx] = lines[last_exec_idx] + " %*"
                    modified = True

        elif full_path.lower().endswith('.sh'):
            if '"$@"' not in content and '$@' not in content:
                last_exec_idx = -1
                for i, line in enumerate(lines):
                    stripped = line.strip().lower()
                    if ('python' in stripped or 'node' in stripped or 'uv run' in stripped or 'pytest' in stripped) \
                       and not stripped.startswith(('echo', '#', 'export', 'if', 'set')) \
                       and ' venv ' not in stripped and ' pip ' not in stripped and ' npm ' not in stripped:
                        last_exec_idx = i
                if last_exec_idx != -1:
                    lines[last_exec_idx] = lines[last_exec_idx] + ' "$@"'
                    modified = True

        if modified:
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines) + '\n')
            except Exception:
                pass

    def _build_command(self, launch_file, args_text):
        """Helper to construct the command line string."""

        if launch_file.endswith('.py'):
            venv_py = get_venv_python_path(self.root_path)
            if os.path.exists(venv_py):
                if is_windows():
                    base_cmd = f'& "{venv_py}" "{launch_file}"'
                else:
                    base_cmd = f'"{venv_py}" "{launch_file}"'
            else:
                base_cmd = f'python "{launch_file}"' if is_windows() else f'python3 "{launch_file}"'

        elif launch_file.endswith(('.bat', '.cmd')):
            if is_windows():
                # Wraps the entire command in quotes for cmd.exe via PowerShell
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
    
    def start_project(self):
        if not self.root_path or self.widget.launch_file_combo.count() == 0:
            return
    
        launch_file = self.widget.launch_file_combo.currentText()
        self.selected_launch_file[self.root_path] = launch_file
        args_text = self.widget.args_input.text().strip()
        self.selected_launch_args[self.root_path] = args_text
    
        full_path = os.path.join(self.root_path, launch_file)
    
        # HTML special case
        if launch_file.endswith('.html'):
            open_file_externally(full_path)
            return

        if args_text:
            self._ensure_args_support(full_path)

    
        final_command = self._build_command(launch_file, args_text)
    
        # Send command to the Console Widget PTY
        if hasattr(self.widget, 'console'):
            # If a session was previously running or stopped, ensure it's fresh or ready
            if not self.widget.console.is_running():
                self.widget.console.start_session()
            self.widget.console.send_external_command(final_command)
    
        self.launch_mode = 'internal'
        self.widget._update_ui_state()
    
    def start_project_external(self):
        """Starts the project in a new system terminal window."""
        if not self.root_path or self.widget.launch_file_combo.count() == 0:
            return
    
        launch_file = self.widget.launch_file_combo.currentText()
        args_text = self.widget.args_input.text().strip()
        full_path = os.path.join(self.root_path, launch_file)
        if launch_file.endswith('.html'):
            open_file_externally(full_path)
            return
        
        full_launch_path = os.path.join(self.root_path, launch_file)

        if args_text:
            self._ensure_args_support(full_launch_path)

        # Construct the base command
        if launch_file.endswith('.py'):
            venv_py = get_venv_python_path(self.root_path)
            py_exe = venv_py if os.path.exists(venv_py) else ("python" if is_windows() else "python3")
            base_cmd = f'"{py_exe}" "{full_launch_path}"'
        elif launch_file.endswith('.js'):
            base_cmd = f'node "{full_launch_path}"'
        elif launch_file.endswith('.sh'):
            base_cmd = f'bash "{full_launch_path}"'
        else:
            base_cmd = f'"{full_launch_path}"'

        # Append arguments properly
        if args_text:
            safe_cmd = f'{base_cmd} {args_text}'
        else:
            safe_cmd = base_cmd

        try:
            if is_windows():
                # Windows specific
                creation_flags = subprocess.CREATE_NEW_CONSOLE
                command_line = f'cmd /k "{safe_cmd}"'

                self.external_process = subprocess.Popen(
                    command_line,
                    cwd=self.root_path,
                    creationflags=creation_flags,
                    shell=False
                )
            else:
                # Linux/Mac
                if sys.platform == 'darwin':
                    self._launch_macos(safe_cmd)
                else:
                    # Linux - use a temporary script to avoid quoting issues
                    import tempfile
                    script_content = f"#!/bin/bash\ncd {shlex.quote(self.root_path)}\n{safe_cmd}\nread -p 'Press Enter to close...' "
                    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.sh', dir=self.root_path, encoding='utf-8') as f:
                        f.write(script_content)
                        os.chmod(f.name, 0o755)
                        temp_file_name = f.name

                    terminals = [
                        ['x-terminal-emulator', '-e', temp_file_name],
                        ['gnome-terminal', '--', temp_file_name],
                        ['konsole', '-e', temp_file_name],
                        ['xfce4-terminal', '-e', temp_file_name],
                        ['xterm', '-e', temp_file_name]
                    ]

                    launched = False
                    for term_cmd in terminals:
                        if shutil.which(term_cmd[0]):
                            subprocess.Popen(term_cmd, cwd=self.root_path)
                            launched = True
                            break

                    if not launched:
                            raise FileNotFoundError("No supported terminal emulator found (tried gnome-terminal, konsole, xfce4-terminal, xterm).")
        
            self.launch_mode = 'external'
            self.widget._update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self.widget, self.lang.get('patch_load_error_title'), f"Failed to launch external: {e}")
    
    def _launch_macos(self, safe_cmd):
        """Helper to launch external terminal on macOS."""
        import tempfile
        script_content = f"#!/bin/bash\ncd {shlex.quote(self.root_path)}\n{safe_cmd}\nread -p 'Press Enter to close...' "
    
        temp_file_name = ""
        # Create temp file that won't be auto-deleted immediately
        # Explicitly set encoding to utf-8 for safety
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.command', dir=self.root_path, encoding='utf-8') as f:
            f.write(script_content)
            os.chmod(f.name, 0o755)
            temp_file_name = f.name
    
        # Execute AFTER closing the file to ensure content is flushed to disk
        if temp_file_name:
            subprocess.call(['open', temp_file_name])
    
    def stop_project(self):
        """Stops the project. Kills external tree or restarts internal console."""
    
        # 1. Handle External Process
        if self.launch_mode == 'external' and self.external_process:
            try:
                # 'start' command on Windows creates a detached process, so self.external_process is just the launcher.
                # However, if we assume the user might have just launched it, we try to be helpful.
                # Since capturing the exact PID of 'start' created window is hard without win32 api,
                # we primarily reset the UI state here, but we try to kill the handle we have.
                parent = psutil.Process(self.external_process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except (psutil.NoSuchProcess, Exception):
                pass
    
            self.external_process = None
            self.launch_mode = None
            self.widget._update_ui_state()
            return
    
        # 2. Handle Internal Process
        # Sending Ctrl+C is often not enough to kill zombies. 
        # The most reliable way to "Stop" a project in a terminal is to kill the shell.
        if hasattr(self.widget, 'console') and self.widget.console.is_running():
            # Restarting the session kills the underlying PowerShell and all its children
            self.widget.console.restart_session()
            # We explicitly clear the 'internal' state
            self.launch_mode = None
            self.widget._update_ui_state()