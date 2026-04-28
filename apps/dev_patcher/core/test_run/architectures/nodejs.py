import os
from systems.os.platform import is_windows
from .base import BaseArchitecture

class NodeJSArchitecture(BaseArchitecture):
    def get_launch_command(self):
        exe = "node" if self.launch_file.endswith(".js") else "ts-node"

        if is_windows():
            return f"& \"{exe}\" \"{self.launch_file}\""
        else:
            return f"\"{exe}\" \"{self.launch_file}\""