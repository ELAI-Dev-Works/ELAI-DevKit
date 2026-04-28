import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.gui.main import MainWindow
from core.gui.launch import LaunchWindow
from systems.error_handler import setup_error_handling
from systems.gui.utils.tooltip_enhancer import setup_tooltip_enhancer
from systems.gui.icons import IconManager

def main():
    """
    Main function to run the GUI application or command-line handlers.
    """

    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    setup_error_handling()
    setup_tooltip_enhancer(app)
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    IconManager.init_paths(app_root)
    app.setWindowIcon(IconManager.get_icon("core.ELAI-DevKit_logo"))

    # 1. Start with LaunchWindow (it initializes the context)
    launcher = LaunchWindow()

    # 2. Check for CLI args using the context created by launcher
    # We use a temporary MainWindow wrapper just for args parsing logic reuse
    # or expose ArgsManager through context.
    # For now, let's keep it simple: if args are present, we might skip launcher.

    # Create a hidden main window to handle args logic
    window = MainWindow(run_gui=False, context=launcher.context)
    
    def handle_args_then_show():
        """
        Handles command-line arguments. After handling, shows the launcher
        unless an argument explicitly requests app exit.
        """
        should_exit = False
    
        if len(sys.argv) > 1:
            handled, should_exit = window.args_manager.parse_and_handle()
            if should_exit:
                # Only quit if handler explicitly requests exit
                app.quit()
                return
    
        # Always show the launcher after handling args (unless exit requested)
        launcher.show()
    
    # Use a single shot timer to run our logic after the event loop has started.
    # This ensures that GUI elements like dialogs can be properly displayed.
    QTimer.singleShot(0, handle_args_then_show)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()