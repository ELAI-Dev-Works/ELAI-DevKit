from ..interface import ProjectBuilderInterface

class ProjectBuilderCoreWindow(ProjectBuilderInterface):
    def __init__(self, context):
        app_instance = context.extension_manager.extensions['project_builder']['instance']
        super().__init__(context, app_instance)

    def project_folder_changed(self, root_path):
        self.app.project_folder_changed(root_path)