from ..interface import ProjectLauncherInterface

class ProjectLauncherCoreWindow(ProjectLauncherInterface):
    """
    Adapter class for integration with the main window.
    """
    def __init__(self, context):
        app_instance = context.extension_manager.extensions['project_launcher']['instance']
        super().__init__(context, app_instance)
        
        # In Core mode, the project selection is handled globally by MainWindow.
        # Hide the local selector to avoid confusion.
        self.project_label.setVisible(False)
        self.project_path_input.setVisible(False)
        self.project_select_btn.setVisible(False)

    def project_folder_changed(self, root_path):
        """Called by MainWindow when the project folder changes."""
        # Use super method to ensure UI updates
        super().project_folder_changed(root_path)