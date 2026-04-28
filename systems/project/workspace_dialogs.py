import os
import shutil
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt

class WorkspaceProjectsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.lang = main_window.lang
        self.workspace_path = main_window.workspace_path
        self.setWindowTitle(self.lang.get('workspace_projects_dialog_title', 'Workspace Projects'))
        self.resize(400, 300)
        self._init_ui()

        from systems.gui.utils.windows import center_window
        center_window(self, main_window)

        self._load_projects()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.rename_btn = QPushButton(self.lang.get('rename_btn', 'Rename'))
        self.rename_btn.clicked.connect(self._rename_project)
        self.delete_btn = QPushButton(self.lang.get('delete_btn', 'Delete'))
        self.delete_btn.clicked.connect(self._delete_project)

        btn_layout.addStretch()
        btn_layout.addWidget(self.rename_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

    def _load_projects(self):
        self.list_widget.clear()
        if not self.workspace_path or not os.path.exists(self.workspace_path):
            return
        for d in sorted(os.listdir(self.workspace_path)):
            if os.path.isdir(os.path.join(self.workspace_path, d)) and not d.startswith('.'):
                item = QListWidgetItem(d)
                item.setData(Qt.ItemDataRole.UserRole, os.path.join(self.workspace_path, d))
                self.list_widget.addItem(item)

    def _rename_project(self):
        item = self.list_widget.currentItem()
        if not item: return
        old_name = item.text()
        old_path = item.data(Qt.ItemDataRole.UserRole)
        
        new_name, ok = QInputDialog.getText(
            self, 
            self.lang.get('rename_project_title', 'Rename Project'),
            self.lang.get('rename_project_prompt', "Enter new name for project '{}':").format(old_name),
            text=old_name
        )
        
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_path = os.path.join(self.workspace_path, new_name.strip())
            if os.path.exists(new_path):
                QMessageBox.warning(self, self.lang.get('patch_load_error_title', 'Error'), "A folder with this name already exists.")
                return
            try:
                os.rename(old_path, new_path)
                self._load_projects()
            except Exception as e:
                QMessageBox.warning(self, self.lang.get('patch_load_error_title', 'Error'), f"Failed to rename: {e}")

    def _delete_project(self):
        item = self.list_widget.currentItem()
        if not item: return
        name = item.text()
        path = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.warning(
            self, 
            self.lang.get('delete_project_warning_title', 'Delete Project'),
            self.lang.get('delete_project_warning_msg', "Are you sure you want to permanently delete the project '{}'? This action cannot be undone!").format(name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                shutil.rmtree(path)
                self._load_projects()
            except Exception as e:
                QMessageBox.warning(self, self.lang.get('patch_load_error_title', 'Error'), f"Failed to delete: {e}")