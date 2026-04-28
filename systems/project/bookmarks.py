import os
import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QMessageBox)
from PySide6.QtCore import Qt

class BookmarksDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.lang = main_window.lang
        self.bookmarks_file = os.path.join(main_window.app_root_path, "user", "bookmarks.json")
        self.bookmarks =[]
        self.setWindowTitle(self.lang.get('bookmarks_title', 'Project Bookmarks'))
        self.resize(500, 400)
        self._init_ui()

        from systems.gui.utils.windows import center_window
        center_window(self, main_window)

        self._load_bookmarks()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(self.lang.get('bookmarks_add_btn', 'Add Current'))
        self.add_btn.clicked.connect(self._add_current)
        self.load_btn = QPushButton(self.lang.get('bookmarks_load_btn', 'Load Selected'))
        self.load_btn.clicked.connect(self._load_selected)
        self.del_btn = QPushButton(self.lang.get('bookmarks_del_btn', 'Delete'))
        self.del_btn.clicked.connect(self._delete_selected)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def _load_bookmarks(self):
        self.list_widget.clear()
        if os.path.exists(self.bookmarks_file):
            try:
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    self.bookmarks = json.load(f)
            except Exception:
                self.bookmarks =[]
        else:
            self.bookmarks =[]

        for b in self.bookmarks:
            mode = b.get('mode', 'Project')
            name = b.get('name', 'Unknown')
            path = b.get('path', '')
            if mode == 'Workspace':
                display = f"[Workspace] {name} ({b.get('subproject', '')})"
            else:
                display = f"[Project] {name} ({path})"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, b)
            self.list_widget.addItem(item)

    def _save_bookmarks(self):
        os.makedirs(os.path.dirname(self.bookmarks_file), exist_ok=True)
        with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
            json.dump(self.bookmarks, f, indent=4)

    def _add_current(self):
        mode = self.main_window.current_mode
        if mode == 'Project':
            if not self.main_window.root_path:
                QMessageBox.warning(self, "Warning", "No project selected.")
                return
            name = os.path.basename(self.main_window.root_path)
            b = {'name': name, 'mode': 'Project', 'path': self.main_window.root_path}
        else:
            if not self.main_window.workspace_path or not self.main_window.root_path:
                QMessageBox.warning(self, "Warning", "No workspace/project selected.")
                return
            name = os.path.basename(self.main_window.workspace_path)
            subproject = os.path.basename(self.main_window.root_path)
            b = {'name': name, 'mode': 'Workspace', 'path': self.main_window.workspace_path, 'subproject': subproject}

        # Check duplicate
        for existing in self.bookmarks:
            if existing.get('mode') == b['mode'] and existing.get('path') == b['path']:
                if mode == 'Project' or existing.get('subproject') == b.get('subproject'):
                    QMessageBox.information(self, "Info", "Bookmark already exists.")
                    return

        self.bookmarks.append(b)
        self._save_bookmarks()
        self._load_bookmarks()

    def _load_selected(self):
        item = self.list_widget.currentItem()
        if not item: return
        b = item.data(Qt.ItemDataRole.UserRole)

        mode = b.get('mode', 'Project')
        path = b.get('path', '')

        if not os.path.exists(path):
            QMessageBox.warning(self, "Warning", f"Path does not exist: {path}")
            return

        self.main_window.mode_combo.setCurrentText(mode)
        if mode == 'Project':
            self.main_window.root_path = path
            self.main_window.workspace_path = None
            self.main_window.path_label.setText(self.main_window.lang.get('project_path_label_selected').format(path))
        else:
            self.main_window.workspace_path = path
            subproj = b.get('subproject', '')
            self.main_window.path_label.setText(self.main_window.lang.get('workspace_label', 'Workspace: {}').format(path))
            self.main_window._scan_workspace()

            self.main_window.workspace_project_combo.blockSignals(True)
            idx = self.main_window.workspace_project_combo.findText(subproj)
            if idx >= 0:
                self.main_window.workspace_project_combo.setCurrentIndex(idx)
                self.main_window.root_path = os.path.join(path, subproj)
            else:
                self.main_window.workspace_project_combo.setCurrentIndex(-1)
                self.main_window.root_path = None
            self.main_window.workspace_project_combo.blockSignals(False)

        self.main_window.edit_ignore_list_button.setEnabled(True)
        self.main_window.theme_manager.update_path_label_style()

        self.main_window._apply_project_change()

        self.accept()

    def _delete_selected(self):
        item = self.list_widget.currentItem()
        if not item: return
        b = item.data(Qt.ItemDataRole.UserRole)
        if b in self.bookmarks:
            self.bookmarks.remove(b)
            self._save_bookmarks()
            self._load_bookmarks()