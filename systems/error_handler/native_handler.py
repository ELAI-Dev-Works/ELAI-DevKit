import faulthandler
import datetime
import sys
from .config import get_crash_log_path

# Keep reference to file so it doesn't get GC'd
_crash_file = None 

def setup_native_handling():
    """
    Enables faulthandler to dump traceback into 'crash_log.txt' 
    on native crashes (SegFault, Access Violation).
    """
    global _crash_file
    
    try:
        crash_path = get_crash_log_path()
        # Open in append mode, but write a header for the new session
        _crash_file = open(crash_path, 'a', encoding='utf-8')
        _crash_file.write(f"\n--- NEW SESSION: {datetime.datetime.now()} ---\n")
        _crash_file.flush()

        # Enable faulthandler
        faulthandler.enable(file=_crash_file, all_threads=True)
        print(f"[ErrorHandler] Native crash logging enabled -> {crash_path}")
    except Exception as e:
        print(f"[ErrorHandler] Failed to setup faulthandler file: {e}")
        # Fallback to stderr
        faulthandler.enable()