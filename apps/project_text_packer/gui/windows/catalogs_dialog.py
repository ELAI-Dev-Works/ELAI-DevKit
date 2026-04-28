import os
import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QMessageBox, QLineEdit, QLabel, QFormLayout)
from PySide6.QtCore import Qt

class CatalogsDialog(QDialog):
    def __init__(self, interface):
        super().__init__(interface)
        self.interface = interface
        self.lang = interface.lang
        self.catalogs_file = os.path.join(interface.app.app_root_path, "user", "catalogs.json")
        self.catalogs =[]
        self.setWindowTitle(self.lang.get('catalogs_title', 'Catalog Categories'))
        self.resize(500, 400)
        self._init_ui()

        from systems.gui.utils.windows import center_window
        center_window(self, interface.main_window)

        self._load_catalogs()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self._on_item_selected)
        layout.addWidget(self.list_widget)

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.comment_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Comment:", self.comment_input)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self._add_catalog)
        self.update_btn = QPushButton("Update")
        self.update_btn.clicked.connect(self._update_catalog)
        self.del_btn = QPushButton("Delete")
        self.del_btn.clicked.connect(self._delete_catalog)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def _get_default_catalogs(self):
        return[
            {"name": "@Packer-ROOT", "comment": "Base output directory", "is_default": True, "path": ""},
            {"name": "@Packer-ROOT/Python", "comment": "Python projects", "is_default": True, "path": "Python"},
            {"name": "@Packer-ROOT/NodeJS", "comment": "NodeJS projects", "is_default": True, "path": "NodeJS"},
            {"name": "@Packer-ROOT/Web", "comment": "HTML5 projects", "is_default": True, "path": "Web"}
        ]

    def _load_catalogs(self):
        self.list_widget.clear()
        if os.path.exists(self.catalogs_file):
            try:
                with open(self.catalogs_file, 'r', encoding='utf-8') as f:
                    self.catalogs = json.load(f)
            except Exception:
                self.catalogs = self._get_default_catalogs()
        else:
            self.catalogs = self._get_default_catalogs()
            self._save_catalogs()

        for c in self.catalogs:
            display = f"{c['name']} | {c['comment']}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, c)
            self.list_widget.addItem(item)

    def _save_catalogs(self):
        os.makedirs(os.path.dirname(self.catalogs_file), exist_ok=True)
        with open(self.catalogs_file, 'w', encoding='utf-8') as f:
            json.dump(self.catalogs, f, indent=4)
        self.interface.load_categories() # update parent combo

    def _on_item_selected(self, current, previous):
        if current:
            c = current.data(Qt.ItemDataRole.UserRole)
            self.name_input.setText(c['name'])
            self.comment_input.setText(c['comment'])

    def _add_catalog(self):
        name = self.name_input.text().strip()
        comment = self.comment_input.text().strip()
        if not name: return
        path = name.replace('@Packer-ROOT/', '').replace('@Packer-ROOT', '').strip('/')
        new_c = {"name": name, "comment": comment, "is_default": False, "path": path}
        self.catalogs.append(new_c)
        self._save_catalogs()
        self._load_catalogs()

    def _update_catalog(self):
        item = self.list_widget.currentItem()
        if not item: return
        c = item.data(Qt.ItemDataRole.UserRole)
        if c.get('is_default'):
            QMessageBox.warning(self, "Warning", "Cannot modify default categories.")
            return

        c['name'] = self.name_input.text().strip()
        c['comment'] = self.comment_input.text().strip()
        c['path'] = c['name'].replace('@Packer-ROOT/', '').replace('@Packer-ROOT', '').strip('/')
        self._save_catalogs()
        self._load_catalogs()

    def _delete_catalog(self):
        item = self.list_widget.currentItem()
        if not item: return
        c = item.data(Qt.ItemDataRole.UserRole)
        if c.get('is_default'):
            QMessageBox.warning(self, "Warning", "Cannot delete default categories.")
            return

        self.catalogs.remove(c)
        self._save_catalogs()
        self._load_catalogs()