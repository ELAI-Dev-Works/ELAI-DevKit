from PySide6.QtWidgets import QPlainTextEdit

class LogBox(QPlainTextEdit):
    """A simple wrapper for the log output widget for better modularity."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setProperty("no_custom_tooltip", True)
        self.setPlaceholderText('execution_result')
        self.setMinimumHeight(50)