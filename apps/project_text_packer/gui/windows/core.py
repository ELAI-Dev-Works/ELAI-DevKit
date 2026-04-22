from ..interface import ProjectTextPackerInterface

class ProjectTextPackerCoreWindow(ProjectTextPackerInterface):
    """
    Adapter class for integration with the main window of ELAI-DevKit.
    Inherits from the main interface and adds specific methods for the tab widget.
    """
    def __init__(self, context):
        # Retrieve the pre-initialized app instance from the extension manager
        app_instance = context.extension_manager.extensions['project_text_packer']['instance']
        super().__init__(context, app_instance)

    def project_folder_changed(self, root_path):
        """Called by MainWindow when the project folder changes."""
        self.app.root_path = root_path