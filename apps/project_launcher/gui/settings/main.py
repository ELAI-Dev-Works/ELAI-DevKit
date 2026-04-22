from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ProjectLauncherSettingsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.lang = main_window.lang
        
        layout = QVBoxLayout(self)
        self.placeholder_label = QLabel(self.lang.get('pl_no_settings_label'))
        layout.addWidget(self.placeholder_label)
        
    # --- Standard settings methods ---
    def retranslate_ui(self):
        self.placeholder_label.setText(self.lang.get('pl_no_settings_label'))

    def store_initial_state(self): pass
    def apply_settings(self): pass
    def get_settings_to_save(self): return {}
    def revert_settings(self): pass
    def reset_to_defaults(self): pass