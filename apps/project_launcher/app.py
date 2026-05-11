import os
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from .core.scanner import ProjectScanner
from .core.scripts import ScriptManager
from .core.system_tools import SystemTools
from .core.executor import ProjectExecutor

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
        
        # Initialize isolated logic executors
        self.executor = ProjectExecutor(self)

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
                return ProjectScanner.scan(fs)

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
        try:
            filename = ScriptManager.create_bootstrap(fs)
            QMessageBox.information(self.widget, self.lang.get('pl_status_done'), self.lang.get('pl_run_bat_created_msg').format(filename))
            self.project_folder_changed(self.root_path)
        except Exception as e:
            QMessageBox.critical(self.widget, self.lang.get('patch_load_error_title'), str(e))

    def open_project_folder(self):
        try:
            SystemTools.open_folder(self.root_path)
        except Exception as e:
            QMessageBox.critical(self.widget, self.lang.get('patch_load_error_title'), f"Failed to open folder: {e}")

    def open_in_vscode(self):
        try:
            SystemTools.open_vscode(self.root_path)
        except Exception as e:
            QMessageBox.critical(self.widget, self.lang.get('patch_load_error_title'), f"Failed to open in VS Code: {e}")

    def start_project(self):
        if not self.root_path or self.widget.launch_file_combo.count() == 0:
            return
    
        launch_file = self.widget.launch_file_combo.currentText()
        self.selected_launch_file[self.root_path] = launch_file
        args_text = self.widget.args_input.text().strip()
        self.selected_launch_args[self.root_path] = args_text

        self.executor.start_internal(launch_file, args_text)

    def start_project_external(self):
        if not self.root_path or self.widget.launch_file_combo.count() == 0:
            return
    
        launch_file = self.widget.launch_file_combo.currentText()
        args_text = self.widget.args_input.text().strip()
        
        self.executor.start_external(launch_file, args_text)

    def stop_project(self):
        """Stops the project. Kills external tree or restarts internal console."""
        self.executor.stop()