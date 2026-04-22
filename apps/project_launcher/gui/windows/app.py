from PySide6.QtWidgets import QMainWindow
from ..interface import ProjectLauncherInterface

class ProjectLauncherWindow(QMainWindow):
    """
    Standalone window for Project Launcher.
    """
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.app = context.extension_manager.extensions['project_launcher']['instance']
        self.lang = context.lang
        
        self.setWindowTitle(self.lang.get('project_launcher_standalone_title'))
        self.resize(700, 600)

        # Main Interface
        self.interface = ProjectLauncherInterface(context, self.app)
        self.setCentralWidget(self.interface)