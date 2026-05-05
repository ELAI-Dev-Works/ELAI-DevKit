import os
import json
import secrets
import threading
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QComboBox, QLineEdit
from .crypto import CryptoPatterns
from .ipc_server import SecurityIPCServer

class SecurityActionDialog(QDialog):
    def __init__(self, action, details, parent=None):
        super().__init__(parent)
        lang = parent.lang if hasattr(parent, 'lang') else None
        title = lang.get('layer2_alert_title') if lang else "Layer 2: Security Alert"
        self.setWindowTitle(title)
        self.result = False
        self.save_rule = False
        self.rule_scope = "Global"
        self.password = ""
        self._init_ui(action, details)

    def _init_ui(self, action, details):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>An application in the sandbox requested an action.</b><br><br><b>Action:</b> {action}<br><b>Details:</b> {details}"))

        self.remember_cb = QCheckBox("Remember this decision (Adds to List)")
        layout.addWidget(self.remember_cb)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["Global", "Current Project"])
        self.scope_combo.setEnabled(False)
        layout.addWidget(self.scope_combo)

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setPlaceholderText("Master Password (Required to save rule)")
        self.pwd_input.setEnabled(False)
        layout.addWidget(self.pwd_input)

        self.remember_cb.toggled.connect(self.scope_combo.setEnabled)
        self.remember_cb.toggled.connect(self.pwd_input.setEnabled)

        btn_layout = QHBoxLayout()
        allow_btn = QPushButton("Allow")
        allow_btn.setStyleSheet("background-color: #23d18b; color: white; font-weight: bold;")
        allow_btn.clicked.connect(self._on_allow)

        deny_btn = QPushButton("Deny")
        deny_btn.setStyleSheet("background-color: #f14c4c; color: white; font-weight: bold;")
        deny_btn.clicked.connect(self._on_deny)

        btn_layout.addWidget(allow_btn)
        btn_layout.addWidget(deny_btn)
        layout.addLayout(btn_layout)

    def _on_allow(self):
        self.result = True
        self.save_rule = self.remember_cb.isChecked()
        self.rule_scope = self.scope_combo.currentText()
        self.password = self.pwd_input.text()
        self.accept()

    def _on_deny(self):
        self.result = False
        self.save_rule = self.remember_cb.isChecked()
        self.rule_scope = self.scope_combo.currentText()
        self.password = self.pwd_input.text()
        self.accept()

class SecurityManager(QObject):
    permission_requested = Signal(str, str, object, object)

    def __init__(self, app_root_path):
        super().__init__()
        self.app_root_path = app_root_path
        self.config_path = os.path.join(app_root_path, 'user', 'security.json')
        self.rules_path = os.path.join(app_root_path, 'user', 'security_rules.json')
        self.is_setup = os.path.exists(self.config_path)
        self.ipc_server = SecurityIPCServer(self)

        self.local_servers = set() # Layer 1: Whitelisted localhosts
        self.rules = self._load_rules()
        self._permission_cache = {}
        self.is_trusted_session = False
        self.current_project_name = "Global"

        self.permission_requested.connect(self._ask_user_slot, Qt.ConnectionType.QueuedConnection)

    def register_local_server(self, port: int):
        """Layer 1: Auto-allows specific local ports discovered in console."""
        self.local_servers.add(port)

    def _load_rules(self):
        if os.path.exists(self.rules_path):
            try:
                with open(self.rules_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception: pass
        return {"Global": {"allow": {}, "deny": {}}}

    def _save_rules(self):
        os.makedirs(os.path.dirname(self.rules_path), exist_ok=True)
        with open(self.rules_path, 'w', encoding='utf-8') as f:
            json.dump(self.rules, f, indent=4)

    def set_current_project(self, project_path):
        if project_path:
            self.current_project_name = os.path.basename(os.path.normpath(project_path))
            if self.current_project_name not in self.rules:
                self.rules[self.current_project_name] = {"allow": {}, "deny": {}}
        else:
            self.current_project_name = "Global"

    def setup(self, password: str, p1: str, p2: str):
        salt = secrets.token_hex(16)
        hashed = CryptoPatterns.hash_password(password, p1, p2, salt)
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({'hash': hashed, 'salt': salt, 'p1': p1, 'p2': p2}, f)
        self.is_setup = True

    def verify(self, password: str) -> bool:
        if not self.is_setup: return False
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            hashed = CryptoPatterns.hash_password(password, data['p1'], data['p2'], data['salt'])
            return hashed == data['hash']
        except Exception:
            return False

    def start_ipc(self):
        self.ipc_server.start()

    def stop_ipc(self):
        self.ipc_server.stop()
        self._permission_cache.clear()

    def get_ipc_port(self) -> int:
        return self.ipc_server.port

    def _check_rules(self, action, details):
        scopes = [self.current_project_name, "Global"]
        for scope in scopes:
            if scope in self.rules:
                if action in self.rules[scope]["deny"] and details in self.rules[scope]["deny"][action]:
                    return False
                if action in self.rules[scope]["allow"] and details in self.rules[scope]["allow"][action]:
                    return True
        return None

    def request_permission(self, action: str, details: str) -> bool:
        if self.is_trusted_session:
            return True

        # Layer 1: Auto-allow local ports
        if "Network" in action:
            for port in self.local_servers:
                if f":{port}" in str(details) or str(port) in str(details):
                    return True

        rule_result = self._check_rules(action, details)
        if rule_result is not None:
            return rule_result

        app = QApplication.instance()
        if not app:
            return True

        result = [False]
        event = threading.Event()

        self.permission_requested.emit(action, details, result, event)
        event.wait()

        return result[0]

    def _ask_user_slot(self, action, details, result, event):
        try:
            # Check rules again in main thread just in case
            rule_result = self._check_rules(action, details)
            if rule_result is not None:
                result[0] = rule_result
                return

            active_window = QApplication.activeWindow()
            dialog = SecurityActionDialog(action, details, parent=active_window)

            if active_window:
                dialog.setParent(active_window, Qt.WindowType.Dialog)

            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(dialog.reject)
            timer.start(60000)

            dialog.exec()
            timer.stop()

            result[0] = dialog.result

            if dialog.save_rule:
                if not self.verify(dialog.password):
                    QMessageBox.critical(active_window, "Security Error", "Invalid Master Password. Rule not saved.")
                else:
                    scope = self.current_project_name if dialog.rule_scope != "Global" else "Global"
                    r_type = "allow" if result[0] else "deny"

                    if action not in self.rules[scope][r_type]:
                        self.rules[scope][r_type][action] = []
                    if details not in self.rules[scope][r_type][action]:
                        self.rules[scope][r_type][action].append(details)
                    self._save_rules()

        except Exception as e:
            print(f"Error showing security dialog: {e}")
        finally:
            event.set()

    def shutdown(self):
        self.stop_ipc()