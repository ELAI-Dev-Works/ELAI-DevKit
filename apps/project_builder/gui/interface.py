import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QFrame, QFormLayout, QSizePolicy, QSpacerItem
    , QComboBox
)
from systems.gui.widgets.log_box import LogBox
from systems.gui.widgets.quick_settings_panel import QuickSettingsPanel
from systems.gui.widgets.task_progress import TaskProgressIndicator

class ProjectBuilderInterface(QWidget):
    def __init__(self, context, app_instance):
        super().__init__()
        self.context = context
        self.main_window = getattr(context, 'main_window', None)
        self.lang = self.context.lang
        self.app = app_instance
        self.app.set_widget(self)

        self.init_ui()
        self.retranslate_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        controls_frame = QFrame()
        controls_layout = QFormLayout(controls_frame)

        self.arch_label = QLabel()
        self.arch_label_val = QLabel("UNKNOWN")
        self.arch_label_val.setStyleSheet("font-weight: bold; color: #29b8db;")
        controls_layout.addRow(self.arch_label, self.arch_label_val)

        self.main_file_label = QLabel()
        self.main_file_input = QComboBox()
        controls_layout.addRow(self.main_file_label, self.main_file_input)

        self.app_name_label = QLabel()
        self.app_name_input = QLineEdit()
        self.app_name_input.setPlaceholderText("Auto (Folder Name)")
        controls_layout.addRow(self.app_name_label, self.app_name_input)

        self.app_version_label = QLabel()
        self.app_version_input = QLineEdit("1.0.0")
        controls_layout.addRow(self.app_version_label, self.app_version_input)

        self.app_icon_label = QLabel()
        self.app_icon_input = QLineEdit()
        self.app_icon_input.setReadOnly(True)
        self.app_icon_input.setPlaceholderText("Optional (.ico, .png, .icns)")
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(self.app_icon_input)
        self.select_icon_button = QPushButton()
        self.select_icon_button.clicked.connect(self.select_app_icon)
        icon_layout.addWidget(self.select_icon_button)
        controls_layout.addRow(self.app_icon_label, icon_layout)

        self.output_dir_label = QLabel()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setReadOnly(True)
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_input)
        self.select_output_button = QPushButton()
        self.select_output_button.clicked.connect(self.select_output_directory)
        output_dir_layout.addWidget(self.select_output_button)
        controls_layout.addRow(self.output_dir_label, output_dir_layout)

        layout.addWidget(controls_frame)

        start_layout = QHBoxLayout()
        start_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.start_button = QPushButton()
        self.start_button.setStyleSheet("background-color: #23d18b; color: white; font-weight: bold; padding: 8px;")
        self.start_button.clicked.connect(self.app.start_build)
        start_layout.addWidget(self.start_button)
        layout.addLayout(start_layout)

        self.quick_settings_panel = QuickSettingsPanel(self.context, extension_name_filter='project_builder')
        layout.addWidget(self.quick_settings_panel)

        self.progress_indicator = TaskProgressIndicator()
        layout.addWidget(self.progress_indicator)

        self.log_box = LogBox()
        layout.addWidget(self.log_box, stretch=1)

    def retranslate_ui(self):
        self.arch_label.setText(self.lang.get('pb_detected_type_label'))
        self.main_file_label.setText(self.lang.get('pb_main_file_label'))
        self.app_name_label.setText(self.lang.get('pb_app_name_label'))
        self.app_version_label.setText(self.lang.get('pb_app_version_label'))
        self.app_icon_label.setText(self.lang.get('pb_app_icon_label'))
        self.select_icon_button.setText(self.lang.get('pb_select_icon_btn'))
        self.output_dir_label.setText(self.lang.get('pb_output_dir_label'))
        self.select_output_button.setText(self.lang.get('pb_select_output_btn'))
        self.start_button.setText(self.lang.get('pb_build_btn'))
        self.progress_indicator.set_status(self.lang.get('pb_status_ready'))
        self.log_box.setPlaceholderText(self.lang.get('pb_log_placeholder'))

    def select_output_directory(self):
        path = QFileDialog.getExistingDirectory(self, self.lang.get('pb_output_dir_label'))
        if path:
            self.output_dir_input.setText(os.path.normpath(path))

    def select_app_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, self.lang.get('pb_select_icon_btn'), "", "Icons (*.ico *.png *.icns);;All Files (*)")
        if path:
            self.app_icon_input.setText(os.path.normpath(path))


    def _update_ui_state(self):
        if self.app.current_arch == "unknown" or self.main_file_input.count() == 0:
            self.start_button.setEnabled(False)
        else:
            self.start_button.setEnabled(True)