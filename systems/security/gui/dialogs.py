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
