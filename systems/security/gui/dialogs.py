from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from ..crypto import CryptoPatterns

class SetupSecurityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Security Setup: First Run")
        self.resize(550, 350)
        self.sm = parent.context.security_manager
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        info = QLabel("<b>Welcome to ELAI-DevKit!</b><br><br>"
                      "To ensure the highest level of security for the AI Sandbox, "
                      "please set up a master password. This password will be used "
                      "for advanced security settings, file encryption, and access control.")
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addSpacing(10)
        
        p_layout = QHBoxLayout()
        self.p1_combo = QComboBox()
        self.p2_combo = QComboBox()
        for k, v in CryptoPatterns.PATTERNS.items():
            self.p1_combo.addItem(v, k)
            self.p2_combo.addItem(v, k)
            
        self.p2_combo.setCurrentIndex(1) # Default to second pattern
        
        p_layout.addWidget(QLabel("Encryption Pattern 1:"))
        p_layout.addWidget(self.p1_combo)
        p_layout.addWidget(QLabel("Pattern 2:"))
        p_layout.addWidget(self.p2_combo)
        layout.addLayout(p_layout)
        
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setPlaceholderText("Enter a strong master password...")
        
        self.pwd_confirm = QLineEdit()
        self.pwd_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_confirm.setPlaceholderText("Confirm master password...")
        
        layout.addWidget(QLabel("Master Password:"))
        layout.addWidget(self.pwd_input)
        layout.addWidget(self.pwd_confirm)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("Save and Continue")
        self.save_btn.setStyleSheet("background-color: #23d18b; color: white; font-weight: bold; padding: 8px 16px;")
        self.save_btn.clicked.connect(self._save)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def _save(self):
        pwd = self.pwd_input.text()
        conf = self.pwd_confirm.text()
        
        if not pwd:
            QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
        if pwd != conf:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
            
        p1 = self.p1_combo.currentData()
        p2 = self.p2_combo.currentData()
        
        self.sm.setup(pwd, p1, p2)
        QMessageBox.information(self, "Success", "Security setup complete!")
        self.accept()
        
    def closeEvent(self, event):
        if not self.sm.is_setup:
            QMessageBox.critical(self, "Error", "You must set up a password to use ELAI-DevKit securely.")
            event.ignore()
        else:
            super().closeEvent(event)

class ChangePasswordDialog(QDialog):
    def __init__(self, security_manager, parent=None):
        super().__init__(parent)
        self.sm = security_manager
        self.lang = parent.lang if hasattr(parent, 'lang') else None
        title = self.lang.get('change_password_title', 'Change Master Password') if self.lang else "Change Master Password"
        self.setWindowTitle(title)
        self.resize(550, 400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel("<b>Change Master Password</b><br><br>"
                      "Enter your current password, and define a new one along with encryption patterns.")
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addSpacing(10)

        self.current_pwd_input = QLineEdit()
        self.current_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_pwd_input.setPlaceholderText("Current master password...")
        layout.addWidget(QLabel("Current Password:"))
        layout.addWidget(self.current_pwd_input)
        layout.addSpacing(10)

        p_layout = QHBoxLayout()
        self.p1_combo = QComboBox()
        self.p2_combo = QComboBox()
        for k, v in CryptoPatterns.PATTERNS.items():
            self.p1_combo.addItem(v, k)
            self.p2_combo.addItem(v, k)

        # Pre-select existing patterns if possible
        try:
            import json
            with open(self.sm.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                idx1 = self.p1_combo.findData(data.get('p1', '1'))
                if idx1 >= 0: self.p1_combo.setCurrentIndex(idx1)
                idx2 = self.p2_combo.findData(data.get('p2', '2'))
                if idx2 >= 0: self.p2_combo.setCurrentIndex(idx2)
        except:
            self.p2_combo.setCurrentIndex(1)

        p_layout.addWidget(QLabel("Encryption Pattern 1:"))
        p_layout.addWidget(self.p1_combo)
        p_layout.addWidget(QLabel("Pattern 2:"))
        p_layout.addWidget(self.p2_combo)
        layout.addLayout(p_layout)

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setPlaceholderText("Enter new master password...")

        self.pwd_confirm = QLineEdit()
        self.pwd_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_confirm.setPlaceholderText("Confirm new master password...")

        layout.addWidget(QLabel("New Master Password:"))
        layout.addWidget(self.pwd_input)
        layout.addWidget(self.pwd_confirm)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Change Password")
        self.save_btn.setStyleSheet("background-color: #23d18b; color: white; font-weight: bold; padding: 8px 16px;")
        self.save_btn.clicked.connect(self._save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _save(self):
        cur = self.current_pwd_input.text()
        pwd = self.pwd_input.text()
        conf = self.pwd_confirm.text()

        if not self.sm.verify(cur):
            QMessageBox.warning(self, "Error", "Current password is incorrect.")
            return
        if not pwd:
            QMessageBox.warning(self, "Error", "New password cannot be empty.")
            return
        if pwd != conf:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return

        p1 = self.p1_combo.currentData()
        p2 = self.p2_combo.currentData()

        self.sm.setup(pwd, p1, p2)
        QMessageBox.information(self, "Success", "Password changed successfully!")
        self.accept()
