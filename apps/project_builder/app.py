import os
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox

from .core.detector import ProjectDetector
from .core.architectures.python import PythonBuilder
from .core.architectures.nodejs import NodeJSBuilder
from .core.architectures.web import WebBuilder

class BuildWorker(QObject):
    log_msg = Signal(str)
    finished = Signal(bool)

    def __init__(self, architecture, root_path, output_dir, main_file, options):
        super().__init__()
        self.architecture = architecture
        self.root_path = root_path
        self.output_dir = output_dir
        self.main_file = main_file
        self.options = options

    def run(self):
        try:
            builder_class = None
            if self.architecture == 'python':
                builder_class = PythonBuilder
            elif self.architecture == 'nodejs':
                builder_class = NodeJSBuilder
            elif self.architecture == 'web':
                builder_class = WebBuilder

            if not builder_class:
                self.log_msg.emit(f"[Error] Unsupported architecture: {self.architecture}")
                self.finished.emit(False)
                return

            # Ensure output dir exists
            os.makedirs(self.output_dir, exist_ok=True)

            builder = builder_class(self.root_path, self.output_dir, self.main_file, self.options, self._emit_log)
            success = builder.build()
            self.finished.emit(success)

        except Exception as e:
            import traceback
            self.log_msg.emit(f"[Critical Error] {e}\n{traceback.format_exc()}")
            self.finished.emit(False)

    def _emit_log(self, msg):
        self.log_msg.emit(msg)


class ProjectBuilderApp(QObject):
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.lang = context.lang
        self.settings_manager = context.settings_manager
        self.widget = None
        self.root_path = None
        self.current_arch = "unknown"
        
        if hasattr(self.context, 'main_window') and self.context.main_window:
             self.root_path = self.context.main_window.root_path

        self.worker_thread = None
        self.worker = None

    def set_widget(self, widget):
        self.widget = widget

    def project_folder_changed(self, root_path):
        self.root_path = root_path
        if self.widget:

            if not self.root_path:
                self.widget._update_ui_state()
                return

            self.widget.log_box.appendPlainText(self.lang.get('pb_log_scanning'))
            detection = ProjectDetector.detect(self.root_path)
            self.current_arch = detection['architecture']
            
            self.widget.arch_label_val.setText(self.current_arch.upper())

            self.widget.main_file_input.clear()
            if detection['main_files']:
                self.widget.main_file_input.addItems(detection['main_files'])

            self.widget.log_box.appendPlainText(self.lang.get('pb_log_detect').format(self.current_arch))
            self.widget.output_dir_input.setText(os.path.normpath(os.path.join(self.root_path, "dist")))
            self.widget._update_ui_state()

    def get_options(self):
        settings = self.settings_manager.get_setting(['apps', 'project_builder', 'quick'], {})
        opts = settings.get('Options', {})
        return {
            'one_file': opts.get('onefile', True),
            'no_console': opts.get('noconsole', False),
            'target_os': opts.get('target_os', 'windows')
        }

    def start_build(self):
        if not self.root_path: return

        output_dir = self.widget.output_dir_input.text()
        main_file = self.widget.main_file_input.currentText()

        if not output_dir or not main_file:
            QMessageBox.warning(self.widget, "Warning", "Output directory and main file must be specified.")
            return

        self.widget.start_button.setEnabled(False)
        self.widget.progress_indicator.start(0, self.lang.get('pb_status_building'))
        self.widget.log_box.clear()

        options = self.get_options()

        app_name = self.widget.app_name_input.text().strip()
        if not app_name:
            app_name = os.path.basename(os.path.normpath(self.root_path))

        options['app_name'] = app_name
        options['app_version'] = self.widget.app_version_input.text().strip() or "1.0.0"
        options['app_icon'] = self.widget.app_icon_input.text().strip()

        self.worker_thread = QThread()
        self.worker = BuildWorker(self.current_arch, self.root_path, output_dir, main_file, options)
        self.worker.moveToThread(self.worker_thread)

        self.worker.log_msg.connect(self.widget.log_box.appendPlainText)
        self.worker.finished.connect(self._on_build_finished)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def _on_build_finished(self, success):
        if success:
            self.widget.progress_indicator.finish(self.lang.get('pb_status_done'))
        else:
            self.widget.progress_indicator.set_error(self.lang.get('pb_status_error'))
            
        self.widget.start_button.setEnabled(True)
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()