from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import QTimer
from plugins.console.console import ConsoleWidget

class TestConsoleWindow(QDialog):
    def __init__(self, temp_dir, launch_cmd, parent, cwd=None):
        super().__init__(parent)
        self.lang = parent.lang
        self.temp_dir = temp_dir
        self.launch_cmd = launch_cmd
        self.cwd = cwd if cwd else temp_dir
        self.final_log = ""

        self.setWindowTitle(self.lang.get('test_console_title', 'Test Run Console'))
        self.resize(850, 650)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.console = ConsoleWidget(self, cwd=self.cwd, lang=self.lang)
        layout.addWidget(self.console, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.stop_btn = QPushButton(self.lang.get('stop_test_run_btn', 'Stop Test Run'))
        self.stop_btn.setStyleSheet("background-color: #f14c4c; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        self.stop_btn.clicked.connect(self._on_stop)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Start terminal and queue the command
        self.console.start_session()
        QTimer.singleShot(600, self._send_cmd)

    def _send_cmd(self):
        self.console.send_external_command(self.launch_cmd)

    def _on_stop(self):
        self.final_log = self.console.display.toPlainText()
        self.console.stop_session_and_reset()
        self.accept()

    def closeEvent(self, event):
        self.final_log = self.console.display.toPlainText()
        self.console.stop_session_and_reset()
        super().closeEvent(event)