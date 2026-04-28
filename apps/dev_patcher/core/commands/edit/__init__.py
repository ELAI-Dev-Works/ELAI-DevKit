from typing import Tuple
from .. import BaseCommand
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

    def validate(self, full_block: str, command_name: str, args: list, content: str, lang) -> list:
        issues =[]
        header = f"<@|{command_name} {' '.join(args)}"
        
        if not any(arg in ('-v1', '-v2') for arg in args):
            corrected_header = f"<@|{command_name} -v2 {' '.join(args)}"
            issues.append({
                "original": full_block, "corrected": full_block.replace(header, corrected_header),
                "description": "Missing algorithm flag (-v1 or -v2). Recommended to use -v2.", "type": "syntax"
            })
            
        path_arg = next((arg for arg in args if not arg.startswith('-') and arg not in ('-v1', '-v2')), None)
        if path_arg and not path_arg.startswith('@ROOT') and not path_arg.startswith('@APP-ROOT'):
            corrected_path = f"@ROOT/{path_arg}" if not path_arg.startswith('/') else f"@ROOT{path_arg}"
            corrected_header = header.replace(path_arg, corrected_path)
            issues.append({
                "original": full_block, "corrected": full_block.replace(header, corrected_header),
                "description": f"The path '{path_arg}' should be prefixed with @ROOT/.", "type": "syntax"
            })

        if "-replace" in args or "-insert" in args:
            if "---new---" not in content:
                corrected_content = content.replace("---end---", "---new---\n\n---end---", 1)
                issues.append({
                    "original": full_block, "corrected": full_block.replace(content, corrected_content),
                    "description": lang.get('correction_edit_missing_new', "Missing '---new---' block."), "type": "syntax"
                })
        if "-remove" in args:
            if "---new---" in content:
                import re
                corrected_content = re.sub(r"---new---.*?(?=---end---)", "", content, flags=re.DOTALL)
                issues.append({
                    "original": full_block, "corrected": full_block.replace(content, corrected_content),
                    "description": lang.get('correction_edit_remove_has_new', "-remove doesn't need '---new---' block."), "type": "syntax"
                })
        return issues