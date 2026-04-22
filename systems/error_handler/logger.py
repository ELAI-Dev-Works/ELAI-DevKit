import sys
import datetime
import traceback
from .config import get_python_log_path

def log_to_file(text: str, is_exception: bool = False):
    """
    Appends text to the main error log file.
    :param text: The message or traceback to log.
    :param is_exception: If True, adds a header with timestamp.
    """
    try:
        log_path = get_python_log_path()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_path, "a", encoding="utf-8") as f:
            if is_exception:
                f.write(f"\n{'='*40}\n")
                f.write(f"PYTHON EXCEPTION DETECTED\n")
                f.write(f"{'='*40}\n")
            else:
                f.write(f"[{timestamp}] ")

            f.write(text + "\n")
    except Exception as e:
        # Fallback to stderr if file logging fails
        print(f"FAILED TO WRITE TO LOG FILE: {e}", file=sys.stderr)

def log_qt_message(msg_type: str, message: str, context_str: str = ""):
    """Logs Qt internal messages."""
    try:
        log_path = get_python_log_path()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [Qt {msg_type}] {message} {context_str}"
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except:
        pass