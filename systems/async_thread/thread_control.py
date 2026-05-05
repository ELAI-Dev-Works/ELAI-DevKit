from typing import Callable, Any
from .backend.python_executor import PythonExecutor
from .backend.python_worker import PythonWorker
from .frontend.qt_executor import QtExecutor
from .frontend.qt_worker import QtWorker
from .exec_priority import TaskPriority
from .frontend.qt_threading import QtThreadManager
from .backend.python_threading import PythonThreadManager

class ThreadControl:
    """Unified API for executing threaded tasks across Qt and Python backends."""

    def __init__(self):
        self.py_executor = PythonExecutor()
        self.qt_executor = QtExecutor()

    def run_in_background(self, fn: Callable, callback: Callable = None, 
                          error_callback: Callable = None, yield_callback: Callable = None,
                          use_qt: bool = True, priority: TaskPriority = TaskPriority.NORMAL, 
                          *args, **kwargs) -> Any:
        """
        Dispatches a task to the Thread Pool. Ideal for finite background tasks.
        If `use_qt` is True, it uses QThreadPool (safe for sending Qt signals).
        If `use_qt` is False, it uses standard Python ThreadPoolExecutor.
        """
        if use_qt:
            worker = QtWorker(fn, *args, **kwargs)
            if callback:
                worker.signals.result.connect(callback)
            if error_callback:
                worker.signals.error.connect(error_callback)
            if yield_callback:
                worker.signals.yielded.connect(yield_callback)
            self.qt_executor.submit(worker, priority)
            return worker
        else:
            worker = PythonWorker(fn, *args, **kwargs)
            if callback:
                worker.add_done_callback(callback)
            if error_callback:
                worker.add_error_callback(error_callback)
            if yield_callback:
                worker.add_yield_callback(yield_callback)
            worker.future = self.py_executor.submit(worker)
            return worker

    def run_dedicated_thread(self, fn: Callable, callback: Callable = None, 
                             error_callback: Callable = None, yield_callback: Callable = None,
                             use_qt: bool = True, thread_name: str = None, 
                             *args, **kwargs) -> Any:
        """
        Spawns a dedicated, standalone thread outside the ThreadPool. 
        Ideal for infinite loops or long-blocking tasks (like PTY readers) to avoid exhausting the pool.
        """
        if use_qt:
            thread = QtThreadManager.run_in_qthread(fn, parent=None, start=False, *args, **kwargs)
            if thread_name: thread.setObjectName(thread_name)
            if callback: thread.result_ready.connect(callback)
            if error_callback: thread.error_occurred.connect(error_callback)
            if yield_callback: thread.yielded.connect(yield_callback)
            thread.start()
            return thread
        else:
            return PythonThreadManager.run_in_thread(
                fn, name=thread_name, result_cb=callback, 
                error_cb=error_callback, yield_cb=yield_callback, 
                *args, **kwargs
            )

    def get_status(self) -> dict:
        """Returns a snapshot of the current thread pool loads."""
        return {
            "py_active_threads": self.py_executor.active_thread_count(),
            "py_pending_tasks": self.py_executor.pending_tasks(),
            "qt_active_threads": self.qt_executor.active_thread_count(),
            "qt_pending_tasks": self.qt_executor.pending_tasks()
        }

    def shutdown(self):
        self.py_executor.shutdown()