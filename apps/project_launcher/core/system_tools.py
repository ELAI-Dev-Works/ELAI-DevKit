import os
import subprocess
from systems.os.platform import open_file_externally

class SystemTools:
    @staticmethod
    def open_folder(root_path):
        if root_path and os.path.isdir(root_path):
            open_file_externally(root_path)

    @staticmethod
    def open_vscode(root_path):
        if root_path and os.path.isdir(root_path):
            subprocess.Popen(
                'code .',
                cwd=root_path,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )