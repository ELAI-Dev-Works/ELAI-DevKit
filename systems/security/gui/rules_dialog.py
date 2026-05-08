from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QMessageBox, QLabel, QTabWidget, QWidget)
from PySide6.QtCore import Qt

class RuleManagerDialog(QDialog):
    def __init__(self, security_manager, parent=None):
        super().__init__(parent)
        self.sm = security_manager
        self.lang = parent.lang if hasattr(parent, 'lang') else None
        title = self.lang.get('rules_dialog_title', 'Allowed / Denied Rules List')
        self.setWindowTitle(title)
        self.resize(600, 400)
        self._init_ui()
        self._load_rules()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        info_text = self.lang.get('rules_dialog_info', 'Manage security rules (Double-click to delete):')
        layout.addWidget(QLabel(info_text))

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Global Tab
        self.global_tab = QWidget()
        global_layout = QVBoxLayout(self.global_tab)
        self.global_list = QListWidget()
        self.global_list.itemDoubleClicked.connect(self._delete_rule)
        global_layout.addWidget(self.global_list)
        global_tab_title = self.lang.get('ignore_tab_global', 'Global List')
        self.tabs.addTab(self.global_tab, global_tab_title)

        # Project Tab
        self.project_tab = QWidget()
        project_layout = QVBoxLayout(self.project_tab)
        self.project_list = QListWidget()
        self.project_list.itemDoubleClicked.connect(self._delete_rule)
        project_layout.addWidget(self.project_list)
        project_tab_title = self.lang.get('ignore_tab_project', 'Current Project List')
        self.tabs.addTab(self.project_tab, project_tab_title)

        btn_layout = QHBoxLayout()
        close_btn = QPushButton(self.lang.get('close_btn_accept', 'Close'))
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _load_rules(self):
        self.global_list.clear()
        self.project_list.clear()
        rules = self.sm.rules

        current_project = self.sm.current_project_name

        for project, project_rules in rules.items():
            target_list = None
            if project == "Global":
                target_list = self.global_list
            elif project == current_project:
                target_list = self.project_list

            if target_list is not None:
                for action, details in project_rules.get("allow", {}).items():
                    for detail in details:
                        item = QListWidgetItem(f"✅ ALLOW | [{project}] {action}: {detail}")
                        item.setData(Qt.UserRole, (project, "allow", action, detail))
                        item.setForeground(Qt.green)
                        target_list.addItem(item)
                for action, details in project_rules.get("deny", {}).items():
                    for detail in details:
                        item = QListWidgetItem(f"❌ DENY  | [{project}] {action}: {detail}")
                        item.setData(Qt.UserRole, (project, "deny", action, detail))
                        item.setForeground(Qt.red)
                        target_list.addItem(item)

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