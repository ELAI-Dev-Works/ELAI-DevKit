from typing import Tuple
from .. import BaseCommand

# Export EditTool from tool.py for backward compatibility if any module imports it from here
from .tool import EditTool

class Command(BaseCommand):
    """
    Command for intelligent editing of text file contents.
    It dynamically calls action modules from the 'execute' subdirectory based on the first argument.
    """

    PRIORITY = 5

    def build_backup(self, args: list, content: str, project_root: str, backup_builder):
        if not args: return
        normalized_args = list(args)
        if normalized_args[0] in ('-v1', '-v2'):
            normalized_args.pop(0)
            if not normalized_args: return

        if len(normalized_args) > 1:
            backup_builder.use("replace", normalized_args[1])


    def execute(self, args: list, content: str, fs_handler) -> Tuple[bool, str]:
        if not args:
            return False, "EDIT command requires arguments (e.g. -replace, -insert)."
    
        # --- Argument Normalization ---
        # Allow syntax: EDIT -v2 -replace file.py
        # Logic: If args[0] is an algorithm flag, move it to the end.
        # This ensures downstream modules (which expect args[0] == action, args[1] == file) work correctly.
        normalized_args = list(args)
        if normalized_args[0] in ('-v1', '-v2'):
            algo_flag = normalized_args.pop(0)
            if not normalized_args:
                return False, f"Algorithm flag '{algo_flag}' specified, but action argument is missing."
            normalized_args.append(algo_flag)
    
        action_arg = normalized_args[0]
        if not action_arg.startswith('-'):
            return False, f"The first argument to EDIT must be a flag: {action_arg}"
    
        action_name = action_arg[1:]
    
        try:
            action_module = self._load_action_module("edit", action_name, __package__, fs_handler.root)
            if action_module:
                return action_module.run(normalized_args, content, fs_handler)
            else:
                return False, f"Unknown argument for EDIT command: {action_arg}"
        except Exception as e:
            import traceback
            return False, f"Error executing action '{action_name}': {e}\n{traceback.format_exc()}"