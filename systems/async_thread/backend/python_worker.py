from typing import Callable, Any

class PythonWorker:
    """A simple task wrapper for standard Python execution."""
    def __init__(self, fn: Callable, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.callbacks = []
        self.error_callbacks = []
        self.yield_callbacks = []
        self.is_cancelled = False
        self.progress_callback = self.kwargs.pop('progress_callback', None)

        if self.kwargs.pop('inject_worker_ref', False):
            self.kwargs['worker_ref'] = self

    def cancel(self):
        """Marks the worker for cancellation. The executing function should periodically check `worker_ref.is_cancelled`."""
        self.is_cancelled = True

    def add_done_callback(self, callback: Callable[[Any], None]):
        self.callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[Exception], None]):
        self.error_callbacks.append(callback)

    def add_yield_callback(self, callback: Callable[[Any], None]):
        self.yield_callbacks.append(callback)

    def execute(self) -> Any:
        try:
            import inspect
            from systems.error_handler.thread_tracer import ThreadTracer

            mod_name = getattr(self.fn, '__module__', 'unknown_module')
            func_name = getattr(self.fn, '__name__', 'unknown_function')

            ThreadTracer.log_action(mod_name, func_name, "Task execution started")

            if self.is_cancelled:
                ThreadTracer.log_action(mod_name, func_name, "Task execution cancelled before start")
                return None

            result = self.fn(*self.args, **self.kwargs)

            # Generator support for real-time yielding
            if inspect.isgenerator(result):
                last_val = None
                try:
                    while True:
                        if self.is_cancelled:
                            break
                        item = next(result)
                        for ycb in self.yield_callbacks:
                            ycb(item)
                        last_val = item
                except StopIteration as e:
                    if e.value is not None:
                        result = e.value
                    else:
                        result = last_val

            for cb in self.callbacks:
                cb(result)

            ThreadTracer.log_action(mod_name, func_name, "Task finished successfully")
            return result
        except Exception as e:
            try:
                from systems.error_handler.thread_tracer import ThreadTracer
                mod_name = getattr(self.fn, '__module__', 'unknown_module')
                func_name = getattr(self.fn, '__name__', 'unknown_function')
                ThreadTracer.log_action(mod_name, func_name, f"Task failed with error: {e}")
            except Exception:
                pass
            if self.error_callbacks:
                for ecb in self.error_callbacks:
                    ecb(e)
            else:
                try:
                    import sys
                    from PySide6.QtCore import QMetaObject, Qt
                    from PySide6.QtWidgets import QApplication
                    from systems.error_handler.python_handler import build_error_report
                    from systems.error_handler.logger import log_to_file

                    exc_type, exc_value, exc_tb = sys.exc_info()
                    report, severity = build_error_report(exc_type, exc_value, exc_tb)
                    log_to_file(f"Unhandled exception in PythonWorker [{severity}]:\n{report}", is_exception=True)

                    app = QApplication.instance()
                    if app:
                        from systems.error_handler.gui.window import show_error_dialog
                        QMetaObject.invokeMethod(app, lambda: show_error_dialog(exc_type, exc_value, report, severity), Qt.ConnectionType.QueuedConnection)
                except Exception:
                    pass
            raise e