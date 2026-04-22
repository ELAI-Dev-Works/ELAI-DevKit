import os

def get_log_dir():
    """Returns the root directory for logs, creating it if it doesn't exist."""
    # Assuming systems/error_handler/config.py -> go up 2 levels to root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    log_dir = os.path.join(root_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def get_python_log_path():
    """Returns the path to the python error log file."""
    return os.path.join(get_log_dir(), "error_log.txt")

def get_crash_log_path():
    """Returns the path to the native crash log file."""
    return os.path.join(get_log_dir(), "crash_log.txt")