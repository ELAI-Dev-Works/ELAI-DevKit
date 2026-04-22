from PySide6.QtWidgets import QMainWindow
from ..interface import DevPatcherInterface

class DevPatcherWindow(QMainWindow):
    """
    Standalone window for DevPatcher.
    """
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.app = context.extension_manager.extensions['dev_patcher']['instance']
        self.lang = context.lang
        
        self.setWindowTitle(self.lang.get('dev_patcher_standalone_title'))
        self.resize(900, 700)

        self.interface = DevPatcherInterface(context, self.app)
        self.setCentralWidget(self.interface)