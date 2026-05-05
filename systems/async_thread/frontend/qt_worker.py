from PySide6.QtCore import QRunnable, QObject, Signal, Slot
from typing import Callable
import traceback
import sys

class WorkerSignals(QObject):
    """Signals for QtWorker."""
    finished = Signal()
    error = Signal(Exception)
    result = Signal(object)
    progress = Signal(int)
    yielded = Signal(object)

class QtWorker(QRunnable):
    """QRunnable wrapper to execute tasks inside Qt's QThreadPool."""
    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        # Add a keyword argument for progress callback if the function supports it
        if 'progress_callback' in kwargs:
            self.kwargs['progress_callback'] = self.signals.progress

        self.is_cancelled = False
        if self.kwargs.pop('inject_worker_ref', False):
            self.kwargs['worker_ref'] = self

    def cancel(self):
        """Marks the worker for cancellation."""
        self.is_cancelled = True

    @Slot()
    def run(self):
        try:
            import inspect
            from systems.error_handler.thread_tracer import ThreadTracer

            mod_name = getattr(self.fn, '__module__', 'unknown_module')
            func_name = getattr(self.fn, '__name__', 'unknown_function')

            ThreadTracer.log_action(mod_name, func_name, "Task execution started")

            if self.is_cancelled:
                ThreadTracer.log_action(mod_name, func_name, "Task execution cancelled before start")
                self.signals.finished.emit()
                return

            result = self.fn(*self.args, **self.kwargs)

            # Generator support for real-time yielding
            if inspect.isgenerator(result):
                last_val = None
                try:
                    while True:
                        if self.is_cancelled:
                            break
                        item = next(result)
                        self.signals.yielded.emit(item)
                        last_val = item
                except StopIteration as e:
                    if e.value is not None:
                        result = e.value
                    else:
                        result = last_val
                self.signals.result.emit(result)
            else:
                self.signals.result.emit(result)

            ThreadTracer.log_action(mod_name, func_name, "Task finished successfully")
        except Exception as e:
            try:
                from systems.error_handler.thread_tracer import ThreadTracer
                mod_name = getattr(self.fn, '__module__', 'unknown_module')
                func_name = getattr(self.fn, '__name__', 'unknown_function')
                ThreadTracer.log_action(mod_name, func_name, f"Task failed with error: {e}")
            except Exception:
                pass
            # Emit error signal (does nothing if no connections)
            self.signals.error.emit(e)
            # Always log the error for diagnostics
            try:
                import sys
                from PySide6.QtCore import QMetaObject, Qt
                from PySide6.QtWidgets import QApplication
                from systems.error_handler.python_handler import build_error_report
                from systems.error_handler.logger import log_to_file

                exctype, value, tb = sys.exc_info()
                report, severity = build_error_report(exctype, value, tb)
                log_to_file(f"Unhandled exception in QtWorker [{severity}]:\n{report}", is_exception=True)

                app = QApplication.instance()
                if app:
                    from systems.error_handler.gui.window import show_error_dialog
                    QMetaObject.invokeMethod(app, lambda: show_error_dialog(exctype, value, report, severity), Qt.ConnectionType.QueuedConnection)
            except Exception:
                pass
        finally:
            self.signals.finished.emit()