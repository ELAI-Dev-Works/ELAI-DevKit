from PySide6.QtCore import QThread, Signal
from typing import Callable

class GenericQThread(QThread):
    """A generic QThread that runs a specific target function."""
    result_ready = Signal(object)
    error_occurred = Signal(Exception)
    yielded = Signal(object)

    def __init__(self, target: Callable, *args, **kwargs):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            import inspect
            from systems.error_handler.thread_tracer import ThreadTracer

            mod_name = getattr(self.target, '__module__', 'unknown_module')
            func_name = getattr(self.target, '__name__', 'unknown_function')
            ThreadTracer.log_action(mod_name, func_name, "QThread dedicated execution started")

            res = self.target(*self.args, **self.kwargs)
            if inspect.isgenerator(res):
                last_val = None
                try:
                    while True:
                        if self.isInterruptionRequested():
                            break
                        item = next(res)
                        self.yielded.emit(item)
                        last_val = item
                except StopIteration as e:
                    if e.value is not None:
                        res = e.value
                    else:
                        res = last_val
                self.result_ready.emit(res)
            else:
                self.result_ready.emit(res)
            ThreadTracer.log_action(mod_name, func_name, "QThread dedicated execution finished successfully")
        except Exception as e:
            try:
                from systems.error_handler.thread_tracer import ThreadTracer
                mod_name = getattr(self.target, '__module__', 'unknown_module')
                func_name = getattr(self.target, '__name__', 'unknown_function')
                ThreadTracer.log_action(mod_name, func_name, f"QThread dedicated execution failed: {e}")
            except Exception:
                pass
            self.error_occurred.emit(e)

class QtThreadManager:
    """Provides utility methods for QThread management."""
    @staticmethod
    def run_in_qthread(target: Callable, parent=None, start=True, *args, **kwargs) -> GenericQThread:
        thread = GenericQThread(target, *args, **kwargs)
        if parent:
            thread.setParent(parent)
        if start:
            thread.start()
        return thread