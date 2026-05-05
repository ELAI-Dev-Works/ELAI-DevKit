# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QFileDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QToolTip


class FullHistoryDialog(QDialog):
    """Dialog to show the full console output with copy and save options."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Console History")
        self.resize(900, 600)
        self.text = text
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(self.text)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy)
        save_btn = QPushButton("Save As...")
        save_btn.clicked.connect(self._save)
        btn_layout.addStretch()
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _copy(self):
        QApplication.clipboard().setText(self.text)
        QToolTip.showText(QCursor.pos(), "Copied!", self)

    def _save(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Console History", "console_history.txt", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text)
                QToolTip.showText(QCursor.pos(), f"Saved to {file_path}", self)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")