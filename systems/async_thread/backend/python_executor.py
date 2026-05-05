from concurrent.futures import ThreadPoolExecutor
from .python_worker import PythonWorker
from ..optimizer import ThreadOptimizer

class PythonExecutor:
    """Executes PythonWorker tasks using a standard ThreadPoolExecutor."""
    def __init__(self):
        max_workers = ThreadOptimizer.get_optimal_thread_count(io_bound=True)
        self.pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="PyBackendWorker")

    def submit(self, worker: PythonWorker):
        return self.pool.submit(worker.execute)

    def shutdown(self):
        self.pool.shutdown(wait=False)

    def active_thread_count(self) -> int:
        """Returns the number of currently active threads in the python pool."""
        return len(self.pool._threads)

    def pending_tasks(self) -> int:
        """Returns the approximate number of tasks waiting in the queue."""
        return self.pool._work_queue.qsize()