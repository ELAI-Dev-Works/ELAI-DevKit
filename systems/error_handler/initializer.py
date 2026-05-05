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
    from .thread_tracer import ThreadTracer
    mod_name = getattr(func, '__module__', 'unknown_module')
    func_name = getattr(func, '__name__', 'unknown_function')
    ThreadTracer.log_action(mod_name, func_name, "Safe execution started")
    try:
        res = func(*args, **kwargs)
        ThreadTracer.log_action(mod_name, func_name, "Safe execution finished successfully")
        return res
    except Exception as e:
        ThreadTracer.log_action(mod_name, func_name, f"Safe execution failed with error: {e}")
        import sys
        from .python_handler import build_error_report
        exc_type, exc_value, exc_tb = sys.exc_info()
        report_str, severity = build_error_report(exc_type, exc_value, exc_tb)
        print(f"Handled error in {func.__name__} [{severity}]:\n{report_str}")
        log_to_file(f"Handled error in {func.__name__} [{severity}]:\n{report_str}", is_exception=True)