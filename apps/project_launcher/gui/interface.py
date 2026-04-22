from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QFormLayout, QComboBox,
    QLineEdit, QFileDialog, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from plugins.console.console import ConsoleWidget
import os

class ProjectLauncherInterface(QWidget):
    def __init__(self, context, app_instance):
        super().__init__()
        if isinstance(context, QWidget):
            self.main_window = context
            self.context = getattr(context, 'context', None)
        else:
            self.context = context
            self.main_window = getattr(context, 'main_window', None)

        self.lang = self.context.lang if self.context else self.main_window.lang
        self.app = app_instance
        self.app.set_widget(self)

        self._init_ui()
        
        # Initialize state
        if self.app.root_path:
            self.project_folder_changed(self.app.root_path)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.input_requirements = {}

        # --- Top controls ---
        controls_frame = QFrame()
        form_layout = QFormLayout(controls_frame)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Project Selector (Visible in Standalone, can be hidden by CoreWindow)
        self.project_select_layout = QHBoxLayout()
        self.project_path_input = QLineEdit()
        self.project_path_input.setReadOnly(True)
        self.project_select_btn = QPushButton("...")
        self.project_select_btn.setFixedWidth(30)
        self.project_select_btn.clicked.connect(self._select_project_manually)
        
        self.project_select_layout.addWidget(self.project_path_input)
        self.project_select_layout.addWidget(self.project_select_btn)
        
        self.project_label = QLabel() # Set in retranslate
        form_layout.addRow(self.project_label, self.project_select_layout)

        # Launch file selection
        self.launch_file_combo = QComboBox()
        self.launch_file_combo.setMinimumWidth(300)
        self.launch_file_label = QLabel()
        form_layout.addRow(self.launch_file_label, self.launch_file_combo)
        self.launch_file_combo.currentIndexChanged.connect(self._update_input_state)

        # Arguments input
        self.args_input = QLineEdit()
        self.args_label = QLabel()
        form_layout.addRow(self.args_label, self.args_input)

        # Status display
        self.status_display_label = QLabel()
        self.status_label_text = QLabel()
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_display_label)
        status_layout.addWidget(self.status_label_text)
        status_layout.addStretch()
        form_layout.addRow(status_layout)

        layout.addWidget(controls_frame)

        # --- Terminal Section ---
        layout.addWidget(QLabel(self.lang.get('pl_console_label')))
        self.console = ConsoleWidget(self, lang=self.lang)
        layout.addWidget(self.console, stretch=1)

        # --- Action Buttons ---
        button_layout = QHBoxLayout()

        self.open_folder_button = QPushButton()
        self.open_folder_button.clicked.connect(self.app.open_project_folder)
        button_layout.addWidget(self.open_folder_button)

        self.open_vscode_button = QPushButton()
        self.open_vscode_button.clicked.connect(self.app.open_in_vscode)
        button_layout.addWidget(self.open_vscode_button)

        button_layout.addStretch()
        self.start_external_button = QPushButton()
        self.start_external_button.clicked.connect(self.app.start_project_external)
        self.start_button = QPushButton()
        self.start_button.clicked.connect(self.app.start_project)
        self.stop_button = QPushButton()
        self.stop_button.clicked.connect(self.app.stop_project)
        button_layout.addWidget(self.start_external_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)
        self.retranslate_ui()
        self._update_ui_state()

    def retranslate_ui(self):
        self.project_label.setText(self.lang.get('project_label'))
        self.launch_file_label.setText(self.lang.get('pl_launch_file_label'))
        self.args_label.setText(self.lang.get('pl_args_label'))
        self.status_display_label.setText(self.lang.get('pl_status_label'))
        self.start_button.setText(self.lang.get('pl_start_btn')).addGUITooltip(self.lang.get('pl_start_tooltip'))
        self.start_external_button.setText(self.lang.get('pl_start_external_btn')).addGUITooltip(self.lang.get('pl_start_external_tooltip'))
        self.stop_button.setText(self.lang.get('pl_stop_btn')).addGUITooltip(self.lang.get('pl_stop_tooltip'))
        self.open_folder_button.setText(self.lang.get('pl_open_folder_btn')).addGUITooltip(self.lang.get('pl_open_folder_tooltip'))
        self.open_vscode_button.setText(self.lang.get('pl_open_vscode_btn')).addGUITooltip(self.lang.get('pl_open_vscode_tooltip'))

        # Tooltip for console
        self.console.display.setToolTip(self.lang.get('pl_console_label'))

        self._update_ui_state()

    def _select_project_manually(self):
        folder = QFileDialog.getExistingDirectory(self, self.lang.get('select_project_folder_btn'))
        if folder:
            self.project_folder_changed(folder)

    def project_folder_changed(self, root_path):
        self.app.project_folder_changed(root_path)
        self.project_path_input.setText(root_path)
        if root_path:
            self.console.set_cwd(root_path)

    def _on_scan_finished(self, files_map, input_reqs):
        self.launch_file_combo.clear()
        self.input_requirements = input_reqs 

        all_files =[]
        if files_map.get('run_bat'):
            all_files.append(files_map['run_bat'])
        all_files.extend(files_map.get('other_bats', []))
        all_files.extend(files_map.get('scripts',[]))

        def sort_key(filename):
            lower_name = filename.lower()
            if 'uv' in lower_name:
                return (0, lower_name)
            elif 'run' in lower_name:
                return (1, lower_name)
            return (2, lower_name)

        all_files.sort(key=sort_key)

        for f in all_files:
            self.launch_file_combo.addItem(f)

        if self.app.root_path in self.app.selected_launch_file:
            self.launch_file_combo.setCurrentText(self.app.selected_launch_file[self.app.root_path])
        elif self.launch_file_combo.count() > 0:
            self.launch_file_combo.setCurrentIndex(0)

        if self.app.root_path in self.app.selected_launch_args:
            self.args_input.setText(self.app.selected_launch_args[self.app.root_path])
        else:
            self.args_input.clear()

        self._update_input_state()
        self.app.worker_thread.quit()
        self._update_ui_state()

    def _update_input_state(self):
        current = self.launch_file_combo.currentText()
        if hasattr(self, 'input_requirements') and current in self.input_requirements:
            needs_input = self.input_requirements[current]
            self.console.enable_input(needs_input)
        else:
            self.console.enable_input(True)

    def _on_scan_error(self, error_message):
        self.status_label_text.setText(self.lang.get('packer_status_error'))
        QMessageBox.critical(self, self.lang.get('patch_load_error_title'), error_message)
        self.app.worker_thread.quit()
        self._update_ui_state()

    def _on_creation_suggestion(self):
        reply = QMessageBox.question(self, self.lang.get('pl_create_bat_title'), self.lang.get('pl_create_bat_q'),
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.app.create_run_bat()

    def _update_ui_state(self):
        if not self.app.root_path:
            self.status_label_text.setText(self.lang.get('pl_no_project_selected'))
            self.status_label_text.setStyleSheet("color: #aaa")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.launch_file_combo.setEnabled(False)
            self.open_folder_button.setEnabled(False)
            self.open_vscode_button.setEnabled(False)
            return

        self.launch_file_combo.setEnabled(True)
        self.open_folder_button.setEnabled(True)
        self.open_vscode_button.setEnabled(True)

        if self.app.launch_mode == 'internal':
            self.status_label_text.setText(self.lang.get('pl_status_running'))
            self.status_label_text.setStyleSheet("color: #23d18b; font-weight: bold;")
            self.stop_button.setEnabled(True)
        elif self.app.launch_mode == 'external':
            self.status_label_text.setText(self.lang.get('pl_status_running_external'))
            self.status_label_text.setStyleSheet("color: #3b8eea; font-weight: bold;")
            self.stop_button.setEnabled(True)
        else:
            self.status_label_text.setText(self.lang.get('pl_status_ready'))
            self.status_label_text.setStyleSheet("")
            self.stop_button.setEnabled(False)

        if self.launch_file_combo.count() > 0:
            self.start_button.setEnabled(True)
            self.start_external_button.setEnabled(True)
        else:
            self.status_label_text.setText(self.lang.get('pl_no_launch_file'))
            self.start_button.setEnabled(False)
            self.start_external_button.setEnabled(False)