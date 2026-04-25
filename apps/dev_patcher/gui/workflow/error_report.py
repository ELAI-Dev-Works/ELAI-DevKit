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

class AICorrectionReportDialog(QDialog):
    def __init__(self, failed_commands, parent):
        super().__init__(parent)
        self.lang = parent.lang
        self.failed_commands = failed_commands
        self.setWindowTitle(self.lang.get('ai_report_dialog_title', 'AI Correction Report'))
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        info_label = QLabel(self.lang.get('ai_report_dialog_info', 'Problematic commands found. They will be skipped.'))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFontFamily("Courier New")
        layout.addWidget(self.report_text)

        self._generate_report()

        button_box = QDialogButtonBox()
        copy_btn = button_box.addButton(self.lang.get('copy_report_btn', 'Copy Report'), QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = button_box.addButton(self.lang.get('close_btn_accept', 'Close'), QDialogButtonBox.ButtonRole.AcceptRole)

        copy_btn.clicked.connect(self._copy_to_clipboard)
        close_btn.clicked.connect(self.accept)

        layout.addWidget(button_box)

    def _generate_report(self):
        msg_key = 'ai_report_msg_multiple' if len(self.failed_commands) > 1 else 'ai_report_msg_single'
        msg_text = self.lang.get(msg_key, 'Command(s) failed.')
        task_text = self.lang.get('ai_report_task', 'Fix the problem.')

        report_parts = []
        report_parts.append(f"[MESSAGE]\n{msg_text}\n")

        for command, error_msg in self.failed_commands:
            cmd_name, args, content = command
            header = f"<@|{cmd_name} {' '.join(args)}"
            block = f"{header}\n{content}\n---end---"

            report_parts.append(f"[COMMAND]\n{block}\n")
            report_parts.append(f"[ERROR]\n{error_msg}\n")

        report_parts.append(f"[TASK]\n{task_text}")

        self.report_text.setPlainText("\n".join(report_parts))

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self.report_text.toPlainText())

def show_ai_correction_report(manager, failed_commands):
    mw = manager.main_window
    if not failed_commands:
        return

    dialog = AICorrectionReportDialog(failed_commands, parent=mw)
    dialog.exec()
