from PySide6.QtCore import QThreadPool
from .qt_worker import QtWorker
from ..exec_priority import TaskPriority

class QtExecutor:
    """Manages execution of QtWorkers via QThreadPool."""
    def __init__(self):
        self.pool = QThreadPool.globalInstance()
        self.active_workers = set()
        # Optionally tweak maxThreadCount using optimizer if needed
        # self.pool.setMaxThreadCount(ThreadOptimizer.get_optimal_thread_count())

    def submit(self, worker: QtWorker, priority: TaskPriority = TaskPriority.NORMAL):
        self.active_workers.add(worker)
        worker.signals.finished.connect(lambda w=worker: self._on_worker_finished(w))
        self.pool.start(worker, int(priority))

    def _on_worker_finished(self, worker: QtWorker):
        self.active_workers.discard(worker)

    def active_thread_count(self) -> int:
        return self.pool.activeThreadCount()

    def pending_tasks(self) -> int:
        """QThreadPool doesn't expose queue size directly. Returns -1 indicating unsupported natively."""
        return -1