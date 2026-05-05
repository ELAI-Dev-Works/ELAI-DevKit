import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QDialogButtonBox, QApplication, QPushButton, QMessageBox, QPlainTextEdit
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
    def __init__(self, failed_commands, parent, manager=None):
        super().__init__(parent)
        self.lang = parent.lang
        self.manager = manager
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

        # --- Custom buttons ---
        load_correct_btn = QPushButton("Load Correct Patch Commands")
        load_correct_btn.clicked.connect(self._on_load_corrected_commands)
        layout.addWidget(load_correct_btn)

        button_box = QDialogButtonBox()
        copy_btn = button_box.addButton(self.lang.get('copy_report_btn', 'Copy Report'), QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = button_box.addButton(self.lang.get('close_btn_accept', 'Close'), QDialogButtonBox.ButtonRole.AcceptRole)

        copy_btn.clicked.connect(self._copy_to_clipboard)
        close_btn.clicked.connect(self.accept)

        layout.addWidget(button_box)

    def _generate_report(self):
        if len(self.failed_commands) > 1:
            msg_text = self.lang.get('ai_report_msg_multiple', 'Command(s) failed.')
        else:
            msg_text = self.lang.get('ai_report_msg_single', 'Command(s) failed.')
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

    def _on_load_corrected_commands(self):
        """Open a dialog where the user can paste corrected commands and apply them to the patch."""
        if not self.manager or not hasattr(self.manager, 'widget'):
            QMessageBox.warning(self, "Error", "Cannot access the patch editor.")
            return

        separator = "\n--- END OF FAILED COMMAND ---\n"
        original_blocks = []
        for command, error_msg in self.failed_commands:
            cmd_name, args, content = command
            header = f"<@|{cmd_name} {' '.join(args)}"
            block = f"{header}\n{content}\n---end---"
            original_blocks.append(block)

        original_text = separator.join(original_blocks)

        dlg = QDialog(self)
        dlg.setWindowTitle("Correct Failed Commands")
        dlg.resize(700, 500)
        layout = QVBoxLayout(dlg)

        label = QLabel("Edit the failed commands below. Correct them and press OK to replace them in the patch.")
        label.setWordWrap(True)
        layout.addWidget(label)

        text_edit = QTextEdit()
        text_edit.setFontFamily("Courier New")
        text_edit.setPlainText(original_text)
        layout.addWidget(text_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)

        if dlg.exec() != QDialog.Accepted:
            return

        corrected_text = text_edit.toPlainText()
        corrected_blocks = corrected_text.split(separator)
        if len(corrected_blocks) != len(original_blocks):
            QMessageBox.warning(self, "Warning",
                "The number of corrected command blocks does not match the original ones. "
                "Please ensure you haven't removed or added the separator lines.")
            return

        patch_editor = self.manager.widget.patch_input
        current_patch = patch_editor.toPlainText()

        new_patch = current_patch
        for old_block, new_block in zip(original_blocks, corrected_blocks):
            if old_block in new_patch:
                new_patch = new_patch.replace(old_block, new_block, 1)
            else:
                QMessageBox.warning(self, "Warning",
                    f"Could not find the original command block:\n{old_block[:100]}...\n"
                    "The patch may have been modified since the report was generated. "
                    "The block was not replaced.")
                return

        patch_editor.setPlainText(new_patch)
        QMessageBox.information(self, "Success",
            "The corrected commands have been applied to the patch. "
            "Review and simulate the patch before applying.")

def show_ai_correction_report(manager, failed_commands):
    mw = manager.main_window
    if not failed_commands:
        return

    dialog = AICorrectionReportDialog(failed_commands, parent=mw, manager=manager)
    dialog.exec()