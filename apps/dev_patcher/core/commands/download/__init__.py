import importlib
from typing import Tuple
from .. import BaseCommand

class Command(BaseCommand):
    """
    Downloads a file from the internet. This class acts as a dispatcher
    to the main execution logic in 'execute/base.py'.
    """
    
    PRIORITY = 3

    def build_backup(self, args: list, content: str, project_root: str, backup_builder):
        if len(args) >= 2:
            backup_builder.use("delete", args[1])

    
    def execute(self, args: list, content: str, fs_handler) -> Tuple[bool, str]:
        try:
            action_module = importlib.import_module(".execute.base", __package__)
            return action_module.run(args, content, fs_handler)
        except ImportError:
            return False, "Failed to load core module for DOWNLOAD command."
        except Exception as e:
            import traceback
            return False, f"Error executing DOWNLOAD command: {e}\n{traceback.format_exc()}"


    def validate(self, full_block: str, command_name: str, args: list, content: str, lang) -> list:
        issues =[]
        if len(args) != 2:
            issues.append({
                "original": full_block,
                "corrected": full_block,
                "description": "DOWNLOAD command requires exactly 2 arguments: URL and destination.",
                "type": "syntax"
            })
        return issues

