import sys
import psutil
import subprocess
import atexit
import threading

class ProcessManager:
    """Utility class for safe cross-platform OS process management."""
    _active_pids = set()
    _pid_lock = threading.Lock()

    @classmethod
    def register_process(cls, pid: int):
        """Registers a process ID to ensure it is killed if the toolkit crashes."""
        with cls._pid_lock:
            cls._active_pids.add(pid)

    @classmethod
    def unregister_process(cls, pid: int):
        """Unregisters a process ID when it finishes normally."""
        with cls._pid_lock:
            cls._active_pids.discard(pid)

    @classmethod
    def cleanup_all_processes(cls):
        """Kills all registered processes. Called on application exit."""
        with cls._pid_lock:
            pids = list(cls._active_pids)
        for pid in pids:
            cls.kill_process_tree(pid, include_parent=True)
    
    @staticmethod
    def kill_process_tree(pid: int, include_parent: bool = True):
        """
        Safely kills a process and all its child processes.
        Crucial for stopping things like 'npm start' or 'pyinstaller' 
        which spawn multiple sub-processes.
        """
        try:
            if sys.platform == 'win32' and include_parent:
                # Native taskkill on Windows guarantees full tree death including cmd/powershell
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                return

            parent = psutil.Process(pid)
            children = parent.children(recursive=True)

            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass

            if include_parent:
                try:
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass
        except (psutil.NoSuchProcess, Exception):
            pass

    @staticmethod
    def get_creation_flags() -> int:
        """Returns flags to spawn a detached/hidden console process on Windows."""
        if sys.platform == 'win32':
            return subprocess.CREATE_NO_WINDOW
        return 0

atexit.register(ProcessManager.cleanup_all_processes)