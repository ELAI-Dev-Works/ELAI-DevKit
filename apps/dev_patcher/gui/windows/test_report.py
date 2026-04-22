from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QApplication, QLabel
)

class TestReportDialog(QDialog):
    """
    A dialog to show the console output from a test run.
    """
    def __init__(self, log_content: str, parent):
        super().__init__(parent)
        self.lang = parent.lang
        self.log_content = log_content
        
        self.setWindowTitle(self.lang.get('test_run_report_title'))
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)
        
        info_label = QLabel(self.lang.get('test_run_report_info'))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        report_text = QTextEdit()
        report_text.setReadOnly(True)
        report_text.setFontFamily("Courier New")
        report_text.setPlainText(self.log_content)
        layout.addWidget(report_text)

        button_box = QDialogButtonBox()
        copy_btn = button_box.addButton(self.lang.get('copy_report_btn'), QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = button_box.addButton(self.lang.get('close_btn_accept'), QDialogButtonBox.ButtonRole.AcceptRole)

        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.log_content))
        close_btn.clicked.connect(self.accept)

        layout.addWidget(button_box)