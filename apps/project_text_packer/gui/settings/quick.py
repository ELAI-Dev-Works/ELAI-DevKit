import tomllib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout,
    QSpacerItem, QSizePolicy, QGroupBox, QFormLayout, QDoubleSpinBox, QLabel
)

default_settings = """[Options]
one_file = false
add_timestamp = true
split_on_limit = true
split_size_mb = 1.0
"""

class ProjectTextPackerQuickSettingsWidget(QWidget):
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

        self.one_file_checkbox = QCheckBox()
        self.timestamp_checkbox = QCheckBox()
        self.split_checkbox = QCheckBox()

        self.split_size_spinbox = QDoubleSpinBox()
        self.split_size_spinbox.setRange(0.1, 100.0)
        self.split_size_spinbox.setSuffix(" MB")
        self.split_size_spinbox.setSingleStep(0.5)
        self.split_size_label = QLabel()

        form_layout.addRow(self.one_file_checkbox)
        form_layout.addRow(self.timestamp_checkbox)
        form_layout.addRow(self.split_checkbox)
        form_layout.addRow(self.split_size_label, self.split_size_spinbox)

        self.split_checkbox.toggled.connect(self.split_size_spinbox.setEnabled)

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
        settings = self.settings_manager.get_setting(['apps', 'project_text_packer', 'quick'], self.defaults)
        options = settings.get('Options', {})
        self.one_file_checkbox.setChecked(options.get('one_file', False))
        self.timestamp_checkbox.setChecked(options.get('add_timestamp', True))
        self.split_checkbox.setChecked(options.get('split_on_limit', True))
        self.split_size_spinbox.setValue(options.get('split_size_mb', 1.0))
        self.split_size_spinbox.setEnabled(self.split_checkbox.isChecked())
    
    def _get_current_settings(self):
        return {
            'Options': {
                'one_file': self.one_file_checkbox.isChecked(),
                'add_timestamp': self.timestamp_checkbox.isChecked(),
                'split_on_limit': self.split_checkbox.isChecked(),
                'split_size_mb': self.split_size_spinbox.value()
            }
        }

    def apply_quick_settings(self):
        self.settings_manager.update_setting(['apps', 'project_text_packer', 'quick'], self._get_current_settings())
        self._log_message(self.lang.get('quick_settings_applied_log', '[Settings] Quick settings applied.'))

    def project_folder_changed(self, root_path):
        self.save_project_button.setEnabled(bool(root_path))

    def save_quick_settings(self, is_project=False):
        self.settings_manager.update_setting(['apps', 'project_text_packer', 'quick'], self._get_current_settings(), is_project)
        if is_project:
            self.settings_manager.save_project_settings()
            self._log_message(self.lang.get('quick_settings_project_saved_log', '[Settings] Project quick settings saved.'))
        else:
            self.settings_manager.save_settings_file()
            self._log_message(self.lang.get('quick_settings_saved_log'))

    def reset_quick_settings(self):
        options = self.defaults.get('Options', {})
        self.one_file_checkbox.setChecked(options.get('one_file', False))
        self.timestamp_checkbox.setChecked(options.get('add_timestamp', True))
        self.split_checkbox.setChecked(options.get('split_on_limit', True))
        self.split_size_spinbox.setValue(options.get('split_size_mb', 1.0))
        self._log_message(self.lang.get('quick_settings_reset_log'))

    def _log_message(self, message):
        if hasattr(self.context, 'main_window') and self.context.main_window:
            if hasattr(self.context.main_window, 'patcher_log_output'):
                self.context.main_window.patcher_log_output.appendPlainText(message)
                return
        app_instance = self.context.extension_manager.extensions['project_text_packer'].get('instance')
        if app_instance and app_instance.widget and hasattr(app_instance.widget, 'log_box'):
             app_instance.widget.log_box.appendPlainText(message)

    def retranslate_ui(self):
        self.options_group.setTitle(self.lang.get('packer_options_group_title'))
        self.one_file_checkbox.setText(self.lang.get('packer_one_file_checkbox')).addGUITooltip(self.lang.get('packer_one_file_tooltip'))
        self.timestamp_checkbox.setText(self.lang.get('packer_timestamp_checkbox')).addGUITooltip(self.lang.get('packer_timestamp_tooltip'))
        self.split_checkbox.setText(self.lang.get('packer_split_checkbox')).addGUITooltip(self.lang.get('packer_split_tooltip'))
        self.split_size_label.setText(self.lang.get('packer_split_size_label', 'Split size limit:'))
        self.split_size_spinbox.setToolTip(self.lang.get('packer_split_size_tooltip', 'Maximum size of a single file in megabytes.'))
        self.reset_button.setText(self.lang.get('reset_quick_settings_btn'))
        self.apply_button.setText(self.lang.get('apply_quick_settings_btn', 'Apply Settings'))
        self.save_project_button.setText(self.lang.get('save_project_btn', 'Save for Current Project'))
        if hasattr(self.context, 'main_window') and self.context.main_window:
            self.save_project_button.setEnabled(bool(self.context.main_window.root_path))
        self.save_button.setText(self.lang.get('save_quick_settings_btn', 'Save Global'))

def get_quick_settings():
    return [
        {
            'id': 'project_text_packer_panel',
            'qs_type': 'panel',
            'title_lang_key': 'project_text_packer_quick_settings_title',
            'widget_class': ProjectTextPackerQuickSettingsWidget
        }
    ]