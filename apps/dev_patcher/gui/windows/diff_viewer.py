import difflib
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PySide6.QtGui import QFont, QColor
from plugins.code_editor.editor import CodeEditor

class DiffViewerDialog(QDialog):
    def __init__(self, parent, file_path, old_text, new_text):
        super().__init__(parent)
        self.setWindowTitle(f"Diff Preview: {file_path}")
        self.setMinimumSize(900, 600)
        self.old_text = old_text
        self.new_text = new_text
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        info_label = QLabel("Visual Diff of proposed changes:")
        layout.addWidget(info_label)

        self.diff_view = CodeEditor()
        # CodeEditor handles styles and fonts correctly via theme
        layout.addWidget(self.diff_view)

        self._populate_diff()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _populate_diff(self):
        lines = list(difflib.unified_diff(
            self.old_text.splitlines(),
            self.new_text.splitlines(),
            fromfile='Original',
            tofile='New',
            lineterm='',
            n=5
        ))

        if not lines:
            self.diff_view.setPlainText("No changes detected.")
            return

        diff_text = '\n'.join(lines)
        self.diff_view.set_diff_text(diff_text)