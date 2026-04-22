import importlib
from typing import Tuple
from .. import BaseCommand

class Command(BaseCommand):
    """
    Performs smart code refactoring using AST analysis.
    """
    PRIORITY = 10 # Execute after file creation (MANAGE) but before text edits (EDIT) might be safer, or after?
    # Actually, Refactor should probably happen after MANAGE/DOWNLOAD but implies complex logic.
    # Let's keep it consistent with EDIT-like priority or slightly earlier if it structural.
    # Priority 5 is EDIT. Let's make REFACTOR 5 as well, handled by order in patch.

    def build_backup(self, args: list, content: str, project_root: str, backup_builder):
        if not args: return
        action_arg = args[0]
        if not action_arg.startswith('-'): return
        action_name = action_arg[1:]

        action_module = self._load_action_module("refactor", action_name, __package__, project_root)
        if action_module and hasattr(action_module, 'build_backup'):
            action_module.build_backup(args, content, project_root, backup_builder)
        else:
            if "---files---" in content:
                files_block = content.split("---files---")[1].split("---")[0].strip()
                for f in files_block.splitlines():
                    if f.strip():
                        backup_builder.use("replace", f.strip())


    def execute(self, args: list, content: str, fs_handler) -> Tuple[bool, str]:
        if not args:
            return False, "REFACTOR requires arguments (e.g., -rename, -inject, -imports)."

        action_arg = args[0]
        if not action_arg.startswith('-'):
            return False, f"The first argument must be a flag: {action_arg}"

        action_name = action_arg[1:]

        try:
            # Load specific action module (rename, inject, imports)
            action_module = self._load_action_module("refactor", action_name, __package__, fs_handler.root)
            if action_module:
                return action_module.run(args, content, fs_handler)
            else:
                return False, f"Unknown argument for REFACTOR command: {action_arg}"
        except Exception as e:
            import traceback
            return False, f"Error executing refactor action '{action_name}': {e}\n{traceback.format_exc()}"