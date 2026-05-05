import os

class ThreadOptimizer:
    """Auto-optimizes the thread pool size based on the system hardware."""
    
    @staticmethod
    def get_optimal_thread_count(io_bound: bool = True) -> int:
        """
        Calculates optimal thread pool size.
        For I/O bound tasks, we can use more threads.
        For CPU bound, it's strictly limited by physical cores.
        """
        cpu_count = os.cpu_count() or 4
        if io_bound:
            return min(32, cpu_count * 4)
        return cpu_count

    @staticmethod
    def get_system_load() -> float:
        """
        Returns an estimated system CPU load percentage (0.0 to 100.0).
        Useful for dynamically throttling heavy background async/thread tasks.
        """
        try:
            if hasattr(os, 'getloadavg'):
                load1, _, _ = os.getloadavg()
                cpu_count = os.cpu_count() or 1
                return min(100.0, (load1 / cpu_count) * 100.0)
            else:
                # Windows fallback (if psutil is in the environment)
                import psutil
                return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 50.0  # Safe fallback assumption if unable to read metrics