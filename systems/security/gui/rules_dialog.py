from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QMessageBox, QLabel)
from PySide6.QtCore import Qt

class RuleManagerDialog(QDialog):
    def __init__(self, security_manager, parent=None):
        super().__init__(parent)
        self.sm = security_manager
        self.lang = parent.lang if hasattr(parent, 'lang') else None
        title = self.lang.get('rules_dialog_title') if self.lang else "Allowed / Denied Rules List"
        self.setWindowTitle(title)
        self.resize(600, 400)
        self._init_ui()
        self._load_rules()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        info_text = self.lang.get('rules_dialog_info') if self.lang else "Manage security rules (Double-click to delete):"
        layout.addWidget(QLabel(info_text))
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._delete_rule)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _load_rules(self):
        self.list_widget.clear()
        rules = self.sm.rules
        for project, project_rules in rules.items():
            for action, details in project_rules.get("allow", {}).items():
                for detail in details:
                    item = QListWidgetItem(f"✅ ALLOW | [{project}] {action}: {detail}")
                    item.setData(Qt.UserRole, (project, "allow", action, detail))
                    item.setForeground(Qt.green)
                    self.list_widget.addItem(item)
            for action, details in project_rules.get("deny", {}).items():
                for detail in details:
                    item = QListWidgetItem(f"❌ DENY  | [{project}] {action}: {detail}")
                    item.setData(Qt.UserRole, (project, "deny", action, detail))
                    item.setForeground(Qt.red)
                    self.list_widget.addItem(item)

    def _delete_rule(self, item):
        project, r_type, action, detail = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Delete Rule", f"Delete this rule?\n{action}: {detail}")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.sm.rules[project][r_type][action].remove(detail)
                self.sm._save_rules()
                self._load_rules()
            except Exception:
                pass