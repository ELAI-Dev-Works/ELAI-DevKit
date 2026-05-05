import os
import threading
import datetime
from .config import get_log_dir

class ThreadTracer:
    """
    A thread-safe tracer that logs asynchronous and concurrent actions
    to help diagnose the "Hell of Abstractions" execution flow.
    """
    _lock = threading.Lock()

    @classmethod
    def log_action(cls, module_name: str, func_name: str, action: str):
        from systems.error_handler.debug import DEBUG_MODE
        if not DEBUG_MODE:
            return

        log_path = os.path.join(get_log_dir(), "thread_processing_log.txt")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        thread_name = threading.current_thread().name

        # Required format:
        # [module file]
        # <function/process>
        # (execution history/operation/action history)
        entry = (
            f"[{module_name}][Thread: {thread_name}]\n"
            f"<{func_name}>\n"
            f"({timestamp}) {action}\n"
            f"{'-'*50}\n"
        )

        with cls._lock:
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(entry)
            except Exception:
                pass