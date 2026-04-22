import difflib
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel
from PySide6.QtGui import QFont, QColor

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

        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Courier New", 10))
        self.diff_view.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
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
            self.diff_view.setTextColor(QColor('#cccccc'))
            self.diff_view.append("No changes detected.")
            return

        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                self.diff_view.setTextColor(QColor('#cccccc'))
                self.diff_view.setFontWeight(QFont.Weight.Bold)
                self.diff_view.append(line)
                self.diff_view.setFontWeight(QFont.Weight.Normal)
            elif line.startswith('@@'):
                self.diff_view.setTextColor(QColor('#569cd6'))
                self.diff_view.append(line)
            elif line.startswith('+'):
                self.diff_view.setTextColor(QColor('#a7ffa7'))
                self.diff_view.append(line)
            elif line.startswith('-'):
                self.diff_view.setTextColor(QColor('#ff9f9f'))
                self.diff_view.append(line)
            else:
                self.diff_view.setTextColor(QColor('#858585'))
                self.diff_view.append(line)