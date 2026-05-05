import sys
import os
import json
import traceback
import datetime
from PySide6.QtWidgets import QApplication
from .logger import log_to_file

# Global flag to prevent recursive error handling loops
_is_handling_error = False

def determine_severity(module_name: str) -> str:
    if "Core" in module_name or "System" in module_name:
        return "Critical"
    elif "App:" in module_name or "Extension:" in module_name:
        return "Specific"
    else:
        # Fallback to Specific if we know it's a plugin, otherwise Critical
        return "Specific" if module_name != "Unknown" else "Critical"

def build_error_report(exc_type, exc_value, exc_tb):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    launch_gui_file = os.path.join(root_dir, "core", "gui", "launch.py")
    app_version = "ELAI-DevKit Unknown Version"

    if os.path.exists(launch_gui_file):
        try:
            with open(launch_gui_file, "r", encoding="utf-8") as f:
                content = f.read()
                import re
                match = re.search(r'version_label\s*=\s*QLabel\(\s*"(.*?)"\s*\)', content)
                if match:
                    version_str = match.group(1)
                    app_version = f"ELAI-DevKit {version_str}"
        except Exception:
            pass # Fallback to default if parsing fails

    tb = traceback.extract_tb(exc_tb)
    if tb:
        last_frame = tb[-1]
        file_path = last_frame.filename
    else:
        file_path = "Unknown"

    module_name = "Core"
    try:
        rel_path = os.path.relpath(file_path, root_dir).replace('\\', '/')
        if rel_path.startswith('apps/'):
            parts = rel_path.split('/')
            if len(parts) > 1:
                app_folder = parts[1]
                meta_file = os.path.join(root_dir, 'apps', app_folder, 'metadata.json')
                if os.path.exists(meta_file):
                    with open(meta_file, 'r', encoding='utf-8') as mf:
                        meta = json.load(mf)
                        module_name = f"{meta.get('name', app_folder)} {meta.get('version', '')}".strip()
                else:
                    module_name = f"App: {app_folder}"
        elif rel_path.startswith('extensions/'):
            parts = rel_path.split('/')
            if len(parts) > 2:
                ext_folder = parts[2]
                meta_file = os.path.join(root_dir, 'extensions', parts[1], ext_folder, 'metadata.json')
                if os.path.exists(meta_file):
                    with open(meta_file, 'r', encoding='utf-8') as mf:
                        meta = json.load(mf)
                        module_name = f"{meta.get('name', ext_folder)} {meta.get('version', '')}".strip()
                else:
                    module_name = f"Extension: {ext_folder}"
    except Exception:
        pass

    severity = determine_severity(module_name)
    message = f"{exc_type.__name__}: {exc_value}" if exc_type else str(exc_value)

    from .action_mapper import ActionMapper
    action_map = ActionMapper.get_current_map()

    details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb)).strip()

    report = (
        f"[DATE-TIME]\n"
        f"{now}\n"
        f"[SEVERITY]\n"
        f"{severity}\n"
        f"[VERSION]\n"
        f"{app_version}\n"
        f"[MODULE]\n"
        f"{module_name}\n"
        f"[FILE]\n"
        f"{file_path}\n"
        f"[MESSAGE]\n"
        f"{message}\n"
        f"[ACTIONS MAP]\n"
        f"{action_map}\n"
        f"[DETAILS]\n"
        f"{details}"
    )
    return report, severity

def global_exception_hook(exc_type, exc_value, exc_tb):
    """
    Global handler for uncaught Python exceptions.
    """
    global _is_handling_error

    # Prevent infinite loops if the error handler itself crashes
    if _is_handling_error:
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    _is_handling_error = True

    try:
        # 1. Format the detailed report
        report_str, severity = build_error_report(exc_type, exc_value, exc_tb)

        # 2. Print to console (stderr)
        sys.stderr.write(report_str + "\n")

        # 3. Log to file
        log_to_file(report_str, is_exception=True)

        # 4. Show GUI Dialog
        # Import here to ensure QApplication is initialized and avoid circular deps
        from systems.error_handler.gui.window import show_error_dialog

        ignored = show_error_dialog(exc_type, exc_value, report_str, severity)

        if ignored:
            _is_handling_error = False
            return # Do not exit! Allow the application to continue running

    except Exception as e:
        print(f"CRITICAL: Error handler failed: {e}", file=sys.stderr)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    _is_handling_error = False
    sys.exit(1)

def setup_python_handling():
    sys.excepthook = global_exception_hook
    import threading
    def thread_exception_hook(args):
        global_exception_hook(args.exc_type, args.exc_value, args.exc_traceback)
    threading.excepthook = thread_exception_hook
    print("[ErrorHandler] Python exception hooking and threading enabled.")