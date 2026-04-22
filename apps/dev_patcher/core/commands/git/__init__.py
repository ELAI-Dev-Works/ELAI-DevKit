import importlib
from typing import Tuple
from .. import BaseCommand

class Command(BaseCommand):
    """
    Executes Git commands. This class acts as a dispatcher
    to the main execution logic in 'execute/base.py'.
    """
    
    PRIORITY = 2

    def build_backup(self, args: list, content: str, project_root: str, backup_builder):
        if not args: return
        if args[0] == 'clone':
            if len(args) >= 2:
                dest = args[-1]
                if dest != '.':
                    backup_builder.use("delete_dir", dest)
        elif args[0] == 'init':
            backup_builder.use("delete_dir", ".git")

    
    def execute(self, args: list, content: str, fs_handler) -> Tuple[bool, str]:
        try:
            action_module = importlib.import_module(".execute.base", __package__)
            return action_module.run(args, content, fs_handler)
        except ImportError:
            return False, "Failed to load core module for GIT command."
        except Exception as e:
            import traceback
            return False, f"Error while running GIT command: {e}\n{traceback.format_exc()}"