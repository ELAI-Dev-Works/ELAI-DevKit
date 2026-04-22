import os
import subprocess
import sys
import psutil
import shlex
import shutil
from PySide6.QtCore import Signal, QObject, QThread
from PySide6.QtWidgets import QMessageBox
from systems.os.platform import is_windows, open_file_externally, get_venv_python_path

class ScannerWorker(QObject):
    """
    Scans the project directory for launchable files in a background thread.
    """
    finished = Signal(dict, dict) # launch_files, metadata
    suggestion = Signal()
    error = Signal(str)
    
    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
    
    def run(self):
        try:
            launch_files = {
                'run_bat': None,
                'other_bats': [],
                'scripts': []
            }
            # Heuristic map: filename -> needs_input (bool)
            input_requirements = {}
            has_requirements = False
    
            if not self.root_path or not os.path.isdir(self.root_path):
                self.finished.emit(launch_files, input_requirements)
                return
    
            input_keywords = [
                b'input(', b'sys.stdin', b'read-host', b'cin >>',
                b'scanf', b'gets', b'readline', b'prompt(',
                b'set /p'
            ]
    
            for item in os.listdir(self.root_path):
                full_path = os.path.join(self.root_path, item)
                if not os.path.isfile(full_path):
                    continue
    
                lower_item = item.lower()
    
                # Check for input requirements
                needs_input = False
                # Only check code files, ignore binaries to avoid reading huge files
                if lower_item.endswith(('.py', '.js', '.ts', '.bat', '.ps1', '.cmd', '.c', '.cpp', '.h', '.sh')):
                    try:
                        with open(full_path, 'rb') as f:
                            content = f.read() # Read binary to avoid encoding issues
                            if any(keyword in content for keyword in input_keywords):
                                needs_input = True
                    except:
                        pass
                
                input_requirements[item] = needs_input
                
                if lower_item == 'run.bat' and is_windows():
                    launch_files['run_bat'] = item
                elif lower_item == 'run.sh' and not is_windows():
                    launch_files['run_bat'] = item # Reuse key for UI compatibility
                elif lower_item.endswith('.bat'):
                    launch_files['other_bats'].append(item)
                elif lower_item.endswith(('.py', '.html', '.exe', '.js', '.ts', '.sh')):
                    launch_files['scripts'].append(item)
                elif lower_item in ('requirements.txt', 'requirements.in', 'package.json'):
                    has_requirements = True
    
            self.finished.emit(launch_files, input_requirements)
    
            if not launch_files['run_bat'] and not launch_files['other_bats'] and has_requirements:
                self.suggestion.emit()
    
        except Exception as e:
            self.error.emit(str(e))

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
        self.worker_thread = None
        
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

            self.worker = ScannerWorker(self.root_path)
            self.worker_thread = QThread()
            self.worker.moveToThread(self.worker_thread)

            self.worker.finished.connect(self.widget._on_scan_finished)
            self.worker.suggestion.connect(self.widget._on_creation_suggestion)
            self.worker.error.connect(self.widget._on_scan_error)

            self.worker_thread.started.connect(self.worker.run)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.start()
        else:
            self.widget._update_ui_state()

    def create_run_bat(self):
        if is_windows():
            filename = "run.bat"
            content = "@echo off\nsetlocal\necho [ELAI] Auto-generated run.bat\n"
            if os.path.exists(os.path.join(self.root_path, 'package.json')):
                 content += "echo Installing dependencies...\ncall npm install\necho Starting...\nnpm start\n"
            else:
                 content += "echo Preparing environment...\npython -m venv .venv\n.\\.venv\\Scripts\\pip.exe install -r requirements.txt\n.\\.venv\\Scripts\\python.exe main.py\n"
            content += "pause\n"
        else:
            filename = "run.sh"
            content = "#!/bin/bash\n\n"
            if os.path.exists(os.path.join(self.root_path, 'package.json')):
                 content += "echo 'Installing dependencies...'\nnpm install\necho 'Starting...'\nnpm start\n"
            else:
                 content += "echo 'Preparing environment...'\npython3 -m venv .venv\n./.venv/bin/pip install -r requirements.txt\n./.venv/bin/python main.py\n"
            content += "read -p 'Press Enter to exit...' arg\n"
        
        file_path = os.path.join(self.root_path, filename)
        
        try:
            # Enforce LF for .sh files (important if creating on Windows for Linux use)
            if filename.endswith('.sh'):
                with open(file_path, 'wb') as f:
                    f.write(content.replace('\r\n', '\n').encode('utf-8'))
            else:
                with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(content)
        
            if not is_windows():
                os.chmod(file_path, 0o755)
        
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

    def _build_command(self, launch_file, args_text):
        """Helper to construct the command line string."""
        cmd_parts = []
    
        if launch_file.endswith('.py'):
            venv_py = get_venv_python_path(self.root_path)
            if os.path.exists(venv_py):
                cmd_parts.append(f'"{venv_py}"')
            else:
                cmd_parts.append("python3" if not is_windows() else "python")
            cmd_parts.append(f'"{launch_file}"')
        
        elif launch_file.endswith(('.bat', '.cmd', '.ps1', '.exe', '.sh')):
            if is_windows():
                cmd_parts.append(f'.\\"{launch_file}"')
            else:
                cmd_parts.append(f'./"{launch_file}"')
        
        elif launch_file.endswith('.html'):
            if is_windows():
                cmd_parts.append(f'Start-Process "{launch_file}"')
            else:
                # For internal console on posix, we can't really "start" html nicely without opening browser
                # But this is for PTY input command... echo URL is safer?
                cmd_parts.append(f'echo "Please open {launch_file} manually"')
    
        elif launch_file.endswith('.js'):
            cmd_parts.append("node")
            cmd_parts.append(f'"{launch_file}"')
    
        elif launch_file.endswith('.ts'):
            cmd_parts.append("ts-node")
            cmd_parts.append(f'"{launch_file}"')
    
        else:
            cmd_parts.append(f'.\\"{launch_file}"')
    
        if args_text:
            cmd_parts.append(args_text)
    
        return " ".join(cmd_parts)
    
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
        cmd_to_run = []
        
        if launch_file.endswith('.py'):
            venv_py = get_venv_python_path(self.root_path)
            py_exe = venv_py if os.path.exists(venv_py) else ("python" if is_windows() else "python3")
            cmd_to_run = [py_exe, full_launch_path]
            if args_text: cmd_to_run.append(args_text)
        elif launch_file.endswith('.js'):
            cmd_to_run = ["node", full_launch_path]
            if args_text: cmd_to_run.append(args_text)
        elif launch_file.endswith('.sh'):
             cmd_to_run = ["bash", full_launch_path]
             if args_text: cmd_to_run.append(args_text)
        else:
            cmd_to_run = [full_launch_path]
            if args_text: cmd_to_run.append(args_text)
        
        try:
            if is_windows():
                # Windows specific
                creation_flags = subprocess.CREATE_NEW_CONSOLE
                # Construct string for cmd /k
                cmd_str = ' '.join(f'"{c}"' for c in cmd_to_run)
                command_line = f'cmd /k "{cmd_str}"'
        
                self.external_process = subprocess.Popen(
                    command_line,
                    cwd=self.root_path,
                    creationflags=creation_flags,
                    shell=False
                )
            else:
                # Linux/Mac
                # Properly quote command for shell execution
                safe_cmd = ' '.join(shlex.quote(arg) for arg in cmd_to_run)
        
                if sys.platform == 'darwin':
                    self._launch_macos(safe_cmd)
                else:
                    # Linux - Try common terminal emulators
                    # Prioritize 'x-terminal-emulator' as it respects user system preferences
                    terminals = [
                        ['x-terminal-emulator', '-e', f'bash -c "{safe_cmd}; read -p \'Press Enter to close...\'"'],
                        ['gnome-terminal', '--', 'bash', '-c', f'{safe_cmd}; read -p "Press Enter to close..."'],
                        ['konsole', '-e', 'bash', '-c', f'{safe_cmd}; read -p "Press Enter to close..."'],
                        ['xfce4-terminal', '-e', f'bash -c "{safe_cmd}; read -p \'Press Enter to close...\'"'],
                        ['xterm', '-e', f'{safe_cmd}; read -p "Press Enter to close..."']
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