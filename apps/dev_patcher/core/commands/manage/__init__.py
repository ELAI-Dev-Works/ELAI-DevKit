from typing import Tuple
from .. import BaseCommand

class Command(BaseCommand):
    """
    Handles file and directory operations like create, move, copy, delete, etc.
    It dynamically calls action modules from the 'execute' subdirectory based on the first argument.
    """
    
    PRIORITY = 4
    
    def get_priority(self, args: list) -> int:
        # Special case: cleanup (delete) should happen AFTER editing (priority 5)
        if args and args[0] == '-delete':
            return 6
        return self.PRIORITY

    def build_backup(self, args: list, content: str, project_root: str, backup_builder):
        if not args: return
        action_arg = args[0]
        if not action_arg.startswith('-'): return
        action_name = action_arg[1:]

        action_module = self._load_action_module("manage", action_name, __package__, project_root)
        if action_module and hasattr(action_module, 'build_backup'):
            action_module.build_backup(args, content, project_root, backup_builder)

    
    def execute(self, args: list, content: str, fs_handler) -> Tuple[bool, str]:
        if not args:
            return False, "MANAGE requires arguments (-create, -move, etc.)."

        action_arg = args[0]
        if not action_arg.startswith('-'):
            return False, f"The first argument to MANAGE must be a flag: {action_arg}"

        action_name = action_arg[1:]  # e.g., 'create'

        try:
            action_module = self._load_action_module("manage", action_name, __package__, fs_handler.root)
            if action_module:
                return action_module.run(args, content, fs_handler)
            else:
                return False, f"Unknown argument for MANAGE command: {action_arg}"
        except Exception as e:
            import traceback
            return False, f"Error executing action '{action_name}': {e}\n{traceback.format_exc()}"