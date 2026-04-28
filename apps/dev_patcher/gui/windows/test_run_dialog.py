import os
import posixpath
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton

class TestFileSelectDialog(QDialog):
    def __init__(self, vfs, parent):
        super().__init__(parent)
        self.vfs = vfs
        self.lang = parent.lang
        self.selected_file = None
        self._init_ui()
        self._populate_files()

    def _init_ui(self):
        self.setWindowTitle(self.lang.get('test_file_select_title', 'Select Launch File'))
        self.resize(400, 100)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(self.lang.get('test_file_select_label', 'Choose a file to test run:')))

        self.combo = QComboBox()
        layout.addWidget(self.combo)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton(self.lang.get('load_btn_text', 'OK'))
        cancel_btn = QPushButton(self.lang.get('cancel_btn_text', 'Cancel'))

        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _populate_files(self):
        valid_exts = ('.py', '.js', '.ts', '.bat', '.cmd', '.sh', '.html', '.exe')
        files =[]
        try:
            for file_path in self.vfs.files.keys():
                rel_path = posixpath.relpath(file_path, self.vfs.root)
                if '/' not in rel_path:
                    if rel_path.lower().endswith(valid_exts):
                        files.append(rel_path)
        except Exception:
            pass

        def sort_key(f):
            l = f.lower()
            if 'run' in l or 'main' in l or 'index' in l: return 0
            return 1

        files.sort(key=sort_key)
        self.combo.addItems(files)

    def _on_ok(self):
        self.selected_file = self.combo.currentText()
        self.accept()