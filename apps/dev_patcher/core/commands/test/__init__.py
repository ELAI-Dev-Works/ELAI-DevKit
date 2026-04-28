from typing import Tuple
from .. import BaseCommand

class Command(BaseCommand):
    """
    A simple command for debugging and outputting information to the log.
    It dynamically calls action modules from the 'execute' subdirectory.
    """
    PRIORITY = 0
    def execute(self, args: list, content: str, fs_handler) -> Tuple[bool, str]:
        if not args:
            return False, "The TEST command requires an argument (e.g. '-print')."

        action_arg = args[0]
        if not action_arg.startswith('-'):
            return False, f"The argument must be a flag starting with '-': {action_arg}"

        action_name = action_arg[1:]

        try:
            action_module = self._load_action_module("test", action_name, __package__, fs_handler)
            if action_module:
                return action_module.run(args, content, fs_handler)
            else:
                return False, f"Unknown argument for TEST command: {action_arg}"
        except Exception as e:
            import traceback
            return False, f"Error executing action '{action_name}': {e}\n{traceback.format_exc()}"


    def validate(self, full_block: str, command_name: str, args: list, content: str, lang) -> list:
        issues =[]
        if not args:
            header = f"<@|{command_name}"
            issues.append({
                "original": full_block,
                "corrected": full_block.replace(header, f"{header} -print"),
                "description": "TEST command requires an argument (e.g. -print).",
                "type": "syntax"
            })
        return issues

