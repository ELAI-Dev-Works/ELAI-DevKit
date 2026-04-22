import unittest
from unittest.mock import patch
import sys
import os
import subprocess
import threading
from PySide6.QtCore import QtMsgType

# Import modules to test
from systems.error_handler.python_handler import global_exception_hook
from systems.error_handler.qt_handler import qt_message_handler
from systems.error_handler.initializer import safe_execute
from systems.error_handler.config import get_crash_log_path

class TestErrorHandler(unittest.TestCase):
    """
    Unit tests for the ELAI-DevKit Error Handler.
    Evaluates Python, Native, Qt, and Threading error handling capabilities.
    """

    @patch('systems.error_handler.python_handler.log_to_file')
    @patch('systems.error_handler.gui.window.show_error_dialog')
    @patch('sys.exit')
    def test_python_exception_hook(self, mock_exit, mock_dialog, mock_log):
        """Tests if unhandled Python exceptions trigger logging and GUI dialog."""
        try:
            1 / 0
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            global_exception_hook(exc_type, exc_value, exc_tb)

        mock_log.assert_called_once()
        mock_dialog.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch('systems.error_handler.qt_handler.log_qt_message')
    def test_qt_message_handler(self, mock_log_qt):
        """Tests if Qt internal warnings are correctly captured and logged."""
        qt_message_handler(QtMsgType.QtWarningMsg, None, "Test Qt Warning")
        mock_log_qt.assert_called_once()
        self.assertEqual(mock_log_qt.call_args[0][0], "Warning")
        self.assertEqual(mock_log_qt.call_args[0][1], "Test Qt Warning")

    @patch('systems.error_handler.initializer.log_to_file')
    def test_safe_execute_success(self, mock_log):
        """Tests safe_execute wrapper with successful execution."""
        def success_func():
            return "Success"
        result = safe_execute(success_func)
        self.assertEqual(result, "Success")
        mock_log.assert_not_called()

    @patch('systems.error_handler.initializer.log_to_file')
    def test_safe_execute_failure(self, mock_log):
        """Tests safe_execute wrapper capturing an exception."""
        def failing_func():
            raise ValueError("Test Safe Execute Error")
        result = safe_execute(failing_func)
        self.assertIsNone(result)
        mock_log.assert_called_once()
        self.assertIn("Handled error in failing_func", mock_log.call_args[0][0])

    def test_native_crash_logging(self):
        """
        Tests if faulthandler successfully logs native crashes (segmentation faults).
        Spawns a subprocess that intentionally segfaults to protect the test runner.
        """
        crash_log = get_crash_log_path()
        initial_size = os.path.getsize(crash_log) if os.path.exists(crash_log) else 0

        # Script that triggers a segfault
        code = (
            "import sys, ctypes, os\n"
            "sys.path.append(os.path.abspath('.'))\n"
            "from systems.error_handler.native_handler import setup_native_handling\n"
            "setup_native_handling()\n"
            "ctypes.string_at(0)\n" # Intentional segfault
        )

        # Run the script in an isolated subprocess
        subprocess.run([sys.executable, "-c", code], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        final_size = os.path.getsize(crash_log) if os.path.exists(crash_log) else 0
        
        # The size should grow because faulthandler writes the traceback
        self.assertGreater(final_size, initial_size, "Crash log should grow after a native segfault.")

    @patch('systems.error_handler.python_handler.log_to_file')
    @patch('systems.error_handler.gui.window.show_error_dialog')
    @patch('sys.exit')
    def test_thread_exception_handling(self, mock_exit, mock_dialog, mock_log):
        """
        Diagnostic test: Proves that standard thread exceptions are caught by the global error handler.
        """
        from systems.error_handler.python_handler import setup_python_handling
        setup_python_handling()

        def crashing_thread():
            raise RuntimeError("Thread Crash")

        t = threading.Thread(target=crashing_thread)
        t.start()
        t.join()

        mock_log.assert_called()

    @patch('systems.error_handler.python_handler.log_to_file')
    @patch('systems.error_handler.gui.window.show_error_dialog')
    @patch('sys.exit')
    def test_qthread_exception_handling(self, mock_exit, mock_dialog, mock_log):
        """
        Diagnostic test: Proves that PySide6 QThread exceptions trigger the global error handler.
        """
        from systems.error_handler.python_handler import setup_python_handling
        from PySide6.QtCore import QThread
        setup_python_handling()

        class CrashingThread(QThread):
            def run(self):
                raise RuntimeError("QThread Crash")

        t = CrashingThread()
        t.start()
        t.wait()

        mock_log.assert_called()

if __name__ == '__main__':
    unittest.main()