# PatcherApp/core/apps/project_text_packer/gui/app_window.py
from PySide6.QtWidgets import QMainWindow
from ..interface import ProjectTextPackerInterface

class ProjectTextPackerWindow(QMainWindow):
    """
    Standalone window for Project Text Packer.
    """
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.app = context.extension_manager.extensions['project_text_packer']['instance']
        self.lang = context.lang
        
        self.setWindowTitle(self.lang.get('project_text_packer_standalone_title'))
        self.resize(600, 500)

        # Main Interface
        self.interface = ProjectTextPackerInterface(context, self.app)
        self.setCentralWidget(self.interface)