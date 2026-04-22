import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, 
    QDialogButtonBox, QApplication, QMessageBox, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class ErrorReportWindow(QDialog):
    """
    A standalone dialog to display critical errors and tracebacks.
    Designed to be robust and minimal dependencies.
    """
    def __init__(self, exc_type, exc_value, traceback_str):
        super().__init__()
        self.setWindowTitle("Critical Error")
        self.setMinimumSize(700, 500)
        self.traceback_str = traceback_str
        
        # --- UI Setup ---
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel(f"<h3>An unhandled exception occurred:</h3><p>{exc_value}</p>")
        header_label.setTextFormat(Qt.TextFormat.RichText)
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # Traceback View
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Courier New", 9))
        self.text_edit.setPlainText(self.traceback_str)
        self.text_edit.setStyleSheet("background-color: #f0f0f0; color: #333; border: 1px solid #ccc;")
        layout.addWidget(self.text_edit)
        
        # Info Label
        info_label = QLabel("A log file has been saved to the application directory.")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("Copy Traceback")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close Application")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.traceback_str)
        QMessageBox.information(self, "Copied", "Traceback copied to clipboard.")

def show_error_dialog(exc_type, exc_value, traceback_str):
    """
    Helper function to safely show the dialog even if the app is unstable.
    """
    # Check if QApplication exists
    app = QApplication.instance()
    if not app:
        # If no app instance (rare, but possible if error during init), create a temp one
        app = QApplication(sys.argv)
        
    window = ErrorReportWindow(exc_type, exc_value, traceback_str)
    window.exec()