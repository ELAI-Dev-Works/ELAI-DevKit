from PySide6.QtWidgets import QFileDialog, QMessageBox

class DevPatcherApp:
    def __init__(self, main_window):
        self.main_window = main_window
        self.lang = main_window.lang
        self.settings_manager = main_window.settings_manager
        self.patch_workflow_manager = None
        self.widget = None

    def set_widget(self, widget):
        self.widget = widget

    

    def load_patch_from_file(self):
        patch_path, _ = QFileDialog.getOpenFileName(self.widget, self.lang.get('load_patch_btn'), "", "DevPatcher Files (*.devpatch);;All Files (*)")
        if patch_path:
            try:
                with open(patch_path, 'r', encoding='utf-8') as f:
                    self.widget.patch_input.setPlainText(f.read())
                self.widget.patcher_log_output.appendPlainText(self.lang.get('patch_loaded_log').format(patch_path))
            except Exception as e:
                QMessageBox.critical(self.widget, self.lang.get('patch_load_error_title'), self.lang.get('patch_load_error_msg').format(e))