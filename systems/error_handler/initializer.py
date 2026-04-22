from .native_handler import setup_native_handling
from .python_handler import setup_python_handling
from .qt_handler import setup_qt_handling
import traceback
from .logger import log_to_file

def setup_error_handling():
    """
    Initializes universal error handling (Native, Python, Qt).
    """
    print("[ErrorHandler] Initializing error subsystems...")
    
    setup_native_handling()
    setup_python_handling()
    setup_qt_handling()

def safe_execute(func, *args, **kwargs):
    """
    Wrapper to execute a function safely and log any exceptions
    without crashing the app (if possible).
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        import sys
        from .python_handler import build_error_report
        exc_type, exc_value, exc_tb = sys.exc_info()
        report_str = build_error_report(exc_type, exc_value, exc_tb)
        print(f"Handled error in {func.__name__}:\n{report_str}")
        log_to_file(f"Handled error in {func.__name__}:\n{report_str}", is_exception=True)