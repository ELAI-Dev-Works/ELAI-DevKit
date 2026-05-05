from PySide6.QtCore import QMetaObject, Qt, QObject, Signal

class SignalBridge(QObject):
    """
    A bridge to safely emit Qt signals from pure Python background threads.
    """
    # Define a generic signal that can carry any payload
    generic_signal = Signal(object, object) # event_name, payload
    progress_signal = Signal(str, int, int) # event_name, current, total
    error_signal = Signal(str, Exception)   # event_name, exception

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generic_signal.connect(self._handle_signal, Qt.ConnectionType.QueuedConnection)
        self.progress_signal.connect(self._handle_progress, Qt.ConnectionType.QueuedConnection)
        self.error_signal.connect(self._handle_error, Qt.ConnectionType.QueuedConnection)

        self.listeners = {}
        self.progress_listeners = {}
        self.error_listeners = {}

    def subscribe(self, event_name: str, callback):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)

    def emit_safe(self, event_name: str, payload=None):
        """Called from ANY thread to safely trigger a callback in the Main GUI thread."""
        self.generic_signal.emit(event_name, payload)

    def _handle_signal(self, event_name, payload):
        """Executes in the main thread."""
        if event_name in self.listeners:
            for cb in self.listeners[event_name]:
                cb(payload)

    def subscribe_progress(self, event_name: str, callback):
        if event_name not in self.progress_listeners:
            self.progress_listeners[event_name] = []
        self.progress_listeners[event_name].append(callback)

    def subscribe_error(self, event_name: str, callback):
        if event_name not in self.error_listeners:
            self.error_listeners[event_name] = []
        self.error_listeners[event_name].append(callback)

    def emit_progress(self, event_name: str, current: int, total: int):
        """Safely emit progress data from background thread to main GUI thread."""
        self.progress_signal.emit(event_name, current, total)

    def emit_error(self, event_name: str, exception: Exception):
        """Safely emit error payloads from background thread to main GUI thread."""
        self.error_signal.emit(event_name, exception)

    def _handle_progress(self, event_name, current, total):
        if event_name in self.progress_listeners:
            for cb in self.progress_listeners[event_name]:
                cb(current, total)

    def _handle_error(self, event_name, exception):
        if event_name in self.error_listeners:
            for cb in self.error_listeners[event_name]:
                cb(exception)