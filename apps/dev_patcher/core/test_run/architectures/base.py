class BaseArchitecture:
    """
    Base class for preparing execution commands inside the temp environment.
    """
    def __init__(self, temp_dir, project_root, launch_file):
        self.temp_dir = temp_dir
        self.project_root = project_root
        self.launch_file = launch_file

    def get_launch_command(self, is_trusted=False):
        raise NotImplementedError("Subclasses must implement this method")

    def _apply_sandbox(self, cmd_list, is_trusted=False):
        from systems.fs.os_bridge.sandbox import OSSandbox
        return OSSandbox.wrap_command(cmd_list, self.temp_dir, is_trusted)