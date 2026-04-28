from .base import BaseArchitecture

class WebArchitecture(BaseArchitecture):
    def get_launch_command(self):
        import os
        target_launch_file = os.path.join(self.temp_dir, self.launch_file)
        return f"HTML:{target_launch_file}"