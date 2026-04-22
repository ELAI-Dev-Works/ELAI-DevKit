import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox, QApplication
from PySide6.QtCore import Qt

class ErrorReportDialog(QDialog):
    """
    A dialog to show failed commands and allow copying the report.
    """
    def __init__(self, failed_commands, title, message, parent):
        super().__init__(parent)
        self.lang = parent.lang
        self.failed_commands = failed_commands
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        info_label = QLabel(message)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFontFamily("Courier New")
        layout.addWidget(self.report_text)

        self._generate_report()

        button_box = QDialogButtonBox()
        copy_btn = button_box.addButton(self.lang.get('copy_report_btn'), QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = button_box.addButton(self.lang.get('close_btn_accept'), QDialogButtonBox.ButtonRole.AcceptRole)

        copy_btn.clicked.connect(self._copy_to_clipboard)
        close_btn.clicked.connect(self.accept)

        layout.addWidget(button_box)

    def _generate_report(self):
        full_report =[]
        for command, error_msg in self.failed_commands:
            cmd_name, args, content = command
            header = f"<@|{cmd_name} {' '.join(args)}"
            block = f"{header}\n{content}\n---end---"

            report_entry = (
                f"--- COMMAND FAILED ---\n"
                f"Error: {error_msg}\n\n"
                f"--- Full Block ---\n"
                f"{block}\n"
                f"{'='*60}\n"
            )
            full_report.append(report_entry)

        self.report_text.setPlainText("\n".join(full_report))

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self.report_text.toPlainText())

def show_error_report(manager, failed_commands):
    mw = manager.main_window
    if not failed_commands:
        return

    dialog = ErrorReportDialog(
        failed_commands,
        mw.lang.get('error_report_title'),
        mw.lang.get('error_report_msg'),
        parent=mw
    )
    dialog.exec()