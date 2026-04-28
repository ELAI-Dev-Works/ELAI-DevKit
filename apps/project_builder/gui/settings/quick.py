import tomllib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout,
    QSpacerItem, QSizePolicy, QGroupBox, QFormLayout, QComboBox, QLabel
)

default_settings = """
[Options]
onefile = true
noconsole = false
target_os = "windows"
"""

class ProjectBuilderQuickSettingsWidget(QWidget):
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.lang = context.lang
        self.settings_manager = context.settings_manager
        self.defaults = tomllib.loads(default_settings)

        self.init_ui()
        self.load_settings()
        self.retranslate_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)

        self.options_group = QGroupBox()
        form_layout = QFormLayout(self.options_group)

        self.onefile_check = QCheckBox()
        self.noconsole_check = QCheckBox()
        
        self.os_combo = QComboBox()
        self.os_combo.addItems(["windows", "linux", "mac"])
        self.os_label = QLabel()

        form_layout.addRow(self.onefile_check)
        form_layout.addRow(self.noconsole_check)
        form_layout.addRow(self.os_label, self.os_combo)

        layout.addWidget(self.options_group)

        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.reset_button = QPushButton()
        self.apply_button = QPushButton()
        self.save_project_button = QPushButton()
        self.save_button = QPushButton()
        self.reset_button.clicked.connect(self.reset_quick_settings)
        self.apply_button.clicked.connect(self.apply_quick_settings)
        self.save_project_button.clicked.connect(lambda: self.save_quick_settings(is_project=True))
        self.save_button.clicked.connect(lambda: self.save_quick_settings(is_project=False))
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.save_project_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

    def load_settings(self):
        settings = self.settings_manager.get_setting(['apps', 'project_builder', 'quick'], self.defaults)
        opts = settings.get('Options', {})
        self.onefile_check.setChecked(opts.get('onefile', True))
        self.noconsole_check.setChecked(opts.get('noconsole', False))
        self.os_combo.setCurrentText(opts.get('target_os', 'windows'))

    def reset_quick_settings(self):
        opts = self.defaults.get('Options', {})
        self.onefile_check.setChecked(opts.get('onefile', True))
        self.noconsole_check.setChecked(opts.get('noconsole', False))
        self.os_combo.setCurrentText(opts.get('target_os', 'windows'))

    def _get_current_settings(self):
        return {
            'Options': {
                'onefile': self.onefile_check.isChecked(),
                'noconsole': self.noconsole_check.isChecked(),
                'target_os': self.os_combo.currentText()
            }
        }

    def apply_quick_settings(self):
        self.settings_manager.update_setting(['apps', 'project_builder', 'quick'], self._get_current_settings())

    def project_folder_changed(self, root_path):
        self.save_project_button.setEnabled(bool(root_path))

    def save_quick_settings(self, is_project=False):
        self.settings_manager.update_setting(['apps', 'project_builder', 'quick'], self._get_current_settings(), is_project)
        if is_project:
            self.settings_manager.save_project_settings()
            if hasattr(self.context, 'main_window') and self.context.main_window:
                self.context.main_window.patcher_log_output.appendPlainText(self.lang.get('quick_settings_project_saved_log', '[Settings] Project quick settings saved.'))
        else:
            self.settings_manager.save_settings_file()
            if hasattr(self.context, 'main_window') and self.context.main_window:
                self.context.main_window.patcher_log_output.appendPlainText(self.lang.get('quick_settings_saved_log', '[Settings] Quick settings saved.'))

    def retranslate_ui(self):
        self.reset_button.setText(self.lang.get('reset_quick_settings_btn', 'Reset to Default'))
        self.apply_button.setText(self.lang.get('apply_quick_settings_btn', 'Apply Settings'))
        self.save_project_button.setText(self.lang.get('save_project_btn', 'Save for Current Project'))
        if hasattr(self.context, 'main_window') and self.context.main_window:
            self.save_project_button.setEnabled(bool(self.context.main_window.root_path))
        self.save_button.setText(self.lang.get('save_quick_settings_btn', 'Save Global'))
        self.options_group.setTitle(self.lang.get('project_builder_quick_settings_title'))
        self.onefile_check.setText(self.lang.get('pb_qs_onefile'))
        self.noconsole_check.setText(self.lang.get('pb_qs_noconsole'))
        self.os_label.setText(self.lang.get('pb_qs_target_os'))

def get_quick_settings():
    return [{
        'id': 'project_builder_panel',
        'qs_type': 'panel',
        'title_lang_key': 'project_builder_quick_settings_title',
        'widget_class': ProjectBuilderQuickSettingsWidget
    }]