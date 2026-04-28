import os
from PySide6.QtCore import Qt
import json
from systems.gui.icons import IconManager
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QFrame, QFormLayout,
            QSizePolicy, QSpacerItem, QComboBox
            )
from systems.gui.widgets.log_box import LogBox
from systems.gui.widgets.quick_settings_panel import QuickSettingsPanel
from apps.project_text_packer.gui.windows.catalogs_dialog import CatalogsDialog
from systems.gui.widgets.task_progress import TaskProgressIndicator

class ProjectTextPackerInterface(QWidget):
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

        self.init_ui()
        self.retranslate_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        controls_frame = QFrame()
        controls_layout = QFormLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.output_dir_input = QComboBox()
        self.output_dir_input.setEditable(True)
        self.load_recent_paths()

        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_input, stretch=1)
        self.select_output_button = QPushButton()
        self.select_output_button.clicked.connect(self.select_output_directory)
        output_dir_layout.addWidget(self.select_output_button)

        self.output_dir_label = QLabel()
        controls_layout.addRow(self.output_dir_label, output_dir_layout)

        self.category_label = QLabel()
        self.category_combo = QComboBox()
        self.edit_categories_btn = QPushButton()
        self.edit_categories_btn.setFixedWidth(30)
        self.edit_categories_btn.clicked.connect(self.open_categories_dialog)
        category_layout = QHBoxLayout()
        category_layout.addWidget(self.category_combo, stretch=1)
        category_layout.addWidget(self.edit_categories_btn)
        controls_layout.addRow(self.category_label, category_layout)

        self.load_categories()


        layout.addWidget(controls_frame)

        start_layout = QHBoxLayout()
        start_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.start_button = QPushButton()
        self.start_button.clicked.connect(self.app.start_pack)
        start_layout.addWidget(self.start_button)
        start_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addLayout(start_layout)

        # Quick Settings
        # Pass context directly, the panel handles V2 logic
        self.quick_settings_panel = QuickSettingsPanel(self.context, extension_name_filter='project_text_packer')
        layout.addWidget(self.quick_settings_panel)
        
        self.progress_indicator = TaskProgressIndicator()
        layout.addWidget(self.progress_indicator)
        
        self.log_box = LogBox()
        layout.addWidget(self.log_box, stretch=1)


    def retranslate_ui(self):
        if hasattr(self.app, 'root_path') and self.main_window:
            if hasattr(self.quick_settings_panel, 'update_icons'):
                self.quick_settings_panel.update_icons()

        self.output_dir_label.setText(self.lang.get('packer_output_dir_label'))

        self.category_label.setText(self.lang.get('packer_category_label', 'Category:'))

        p = self.main_window.theme_manager.current_palette if hasattr(self.main_window, 'theme_manager') else {}
        icon_color = p.get("icon_default", "#e0e0e0")
        self.edit_categories_btn.setIcon(IconManager.get_icon("project_text_packer.categories", icon_color))

        self.select_output_button.setText(self.lang.get('packer_select_output_dir_btn')).addGUITooltip(self.lang.get('packer_select_output_dir_tooltip'))
        self.start_button.setText(self.lang.get('packer_start_btn')).addGUITooltip(self.lang.get('packer_start_tooltip'))
        self.progress_indicator.set_status(self.lang.get('packer_status_ready'))
        self.log_box.setPlaceholderText(self.lang.get('packer_log_placeholder'))
        self.log_box.setToolTip(self.lang.get('packer_log_placeholder'))

    def load_recent_paths(self):
        user_dir = os.path.join(self.app.app_root_path, "user")
        self.history_file = os.path.join(user_dir, "packer_paths.json")
        self.recent_paths = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.recent_paths = json.load(f)
            except:
                pass
        self.output_dir_input.clear()
        self.output_dir_input.addItems(self.recent_paths)

    def save_recent_path(self, path):
        if not path: return
        if path in self.recent_paths:
            self.recent_paths.remove(path)
        self.recent_paths.insert(0, path)
        self.recent_paths = self.recent_paths[:5]

        self.output_dir_input.blockSignals(True)
        self.output_dir_input.clear()
        self.output_dir_input.addItems(self.recent_paths)
        self.output_dir_input.setCurrentText(path)
        self.output_dir_input.blockSignals(False)

    def load_categories(self):
        self.category_combo.clear()
        catalogs_file = os.path.join(self.app.app_root_path, "user", "catalogs.json")
        if os.path.exists(catalogs_file):
            try:
                with open(catalogs_file, 'r', encoding='utf-8') as f:
                    catalogs = json.load(f)
            except Exception:
                catalogs = []
        else:
            catalogs =[
                {"name": "@Packer-ROOT", "comment": "Base output directory", "is_default": True, "path": ""},
                {"name": "@Packer-ROOT/Python", "comment": "Python projects", "is_default": True, "path": "Python"},
                {"name": "@Packer-ROOT/NodeJS", "comment": "NodeJS projects", "is_default": True, "path": "NodeJS"},
                {"name": "@Packer-ROOT/Web", "comment": "HTML5 projects", "is_default": True, "path": "Web"}
            ]

        for c in catalogs:
            self.category_combo.addItem(f"{c['name']} | {c['comment']}", c['path'])

    def open_categories_dialog(self):
        dialog = CatalogsDialog(self)
        dialog.exec()


        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_paths, f, indent=4)
        except:
            pass

    def select_output_directory(self):
        path = QFileDialog.getExistingDirectory(self, self.lang.get('packer_output_dir_label'))
        if path:
            norm_path = os.path.normpath(path)
            self.output_dir_input.setCurrentText(norm_path)
            self.save_recent_path(norm_path)

    def on_packing_finished(self, created_files_msg):
        self.progress_indicator.finish(self.lang.get('packer_status_done'))
        self.log_box.appendPlainText(f"\n{self.lang.get('packer_status_done')}")
        self.start_button.setEnabled(True)
        if self.app.worker_thread:
            self.app.worker_thread.quit()
            self.app.worker_thread.wait()
        QMessageBox.information(self, self.lang.get('packer_status_done'), f"{self.lang.get('packer_log_files_saved')}:\n{created_files_msg}")
    
    def on_packing_error(self, error_msg):
        self.progress_indicator.set_error(self.lang.get('packer_status_error'))
        self.log_box.appendPlainText(f"\nERROR:\n{error_msg}")
        self.start_button.setEnabled(True)
        if self.app.worker_thread:
            self.app.worker_thread.quit()
            self.app.worker_thread.wait()
        QMessageBox.critical(self, self.lang.get('patch_load_error_title'), error_msg)