import sys
import os
import threading
import atexit

class ActionMapper:
    """
    ELAI-DevKit global session action profiler.
    Records all significant function calls from the moment the script is launched.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')).replace('\\', '/')
        self.log_path = os.path.join(self.root_path, 'logs', 'run_log.txt')
        self.actions =[]
        self.last_file = None
        self.is_running = False

        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    @classmethod
    def start(cls, clear_log=False):
        from systems.error_handler.debug import DEBUG_MODE
        if not DEBUG_MODE:
            return

        if cls._instance is None:
            cls._instance = cls()

        with cls._lock:
            if clear_log:
                with open(cls._instance.log_path, 'w', encoding='utf-8') as f:
                    f.write("[ACTIONS MAP] - Session Start\n")
            else:
                with open(cls._instance.log_path, 'a', encoding='utf-8') as f:
                    f.write("\n[ACTIONS MAP] - Subprocess App Spawned\n")

        cls._instance.is_running = True
        sys.setprofile(cls._instance._profile_func)
        threading.setprofile(cls._instance._profile_func)
        atexit.register(cls.flush)

    @classmethod
    def flush(cls):
        if cls._instance and cls._instance.actions:
            with cls._lock:
                if cls._instance.actions:
                    try:
                        with open(cls._instance.log_path, 'a', encoding='utf-8') as f:
                            f.write("".join(cls._instance.actions))
                        cls._instance.actions.clear()
                    except Exception:
                        pass

    @classmethod
    def get_current_map(cls, tail_length=1500):
        """Returns the tail of the current error log action map."""
        cls.flush()
        if not cls._instance:
            return "Action Map unavailable."
        try:
            with open(cls._instance.log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return "..." + content[-tail_length:] if len(content) > tail_length else content
        except Exception:
            return "Action Map unavailable."

    def _profile_func(self, frame, event, arg):
        if event == 'call':
            code = frame.f_code
            filename = code.co_filename.replace('\\', '/')
            
            # Filtering external libraries and hidden functions for a cleaner map
            if filename.startswith(self.root_path) and ".venv" not in filename and "site-packages" not in filename:
                if "action_mapper.py" in filename: return
                
                func_name = code.co_name
                if func_name.startswith('<'): return
                if func_name.startswith('_') and func_name != '__init__': return

                rel_path = filename[len(self.root_path):].lstrip('/')
                
                with self._lock:
                    if self.last_file != rel_path:
                        if self.actions and not self.actions[-1].endswith('\n'):
                            self.actions.append("\n")
                        self.actions.append(f"<{rel_path}> ")
                        self.last_file = rel_path
                    
                    self.actions.append(f"{func_name} -> ")
                    
                    # Packet writing to minimize I/O
                    if len(self.actions) > 200:
                        try:
                            with open(self.log_path, 'a', encoding='utf-8') as f:
                                f.write("".join(self.actions))
                            self.actions.clear()
                        except Exception:
                            pass
        return None