from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtCore import Qt, QTimer

class TaskProgressIndicator(QWidget):
    """
    A reusable widget combining a progress bar and a status label.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

        # Timer to auto-hide the widget after completion
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.reset)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

    def start(self, total=0, status_text="Processing..."):
        """Shows the widget and resets progress."""
        self.hide_timer.stop()  # Stop any pending hide action
        self.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText(status_text)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)

    def update_progress(self, value, status_text=None):
        """Updates the progress bar value and optionally the text."""
        self.progress_bar.setValue(value)
        if status_text:
            self.status_label.setText(status_text)

    def set_status(self, text):
        """Updates only the status text."""
        self.status_label.setVisible(True)
        self.status_label.setText(text)

    def finish(self, status_text="Done", auto_hide=True, delay=1000):
        """Sets progress to max, updates status, and optionally schedules hiding."""
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText(status_text)

        if auto_hide:
            self.hide_timer.start(delay)

    def reset(self):
        """Hides and resets the widget."""
        self.hide_timer.stop()
        self.progress_bar.setVisible(False)
        self.progress_bar.reset()
        self.status_label.clear()
        self.status_label.setVisible(False)
        # Optional: Hide the container itself if it takes up layout space
        # self.setVisible(False) 

    def set_error(self, message):
        """Displays an error message."""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(True)
        self.status_label.setText(message)