from typing import Tuple
from .. import BaseCommand

class Command(BaseCommand):
    """
    Handles file and directory operations like create, move, copy, delete, etc.
    It dynamically calls action modules from the 'execute' subdirectory based on the first argument.
    """

    PRIORITY = 4

    def get_priority(self, args: list) -> int:
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

        action_name = action_arg[1:]

        try:
            action_module = self._load_action_module("manage", action_name, __package__, fs_handler.root)
            if action_module:
                return action_module.run(args, content, fs_handler)
            else:
                return False, f"Unknown argument for MANAGE command: {action_arg}"
        except Exception as e:
            import traceback
            return False, f"Error executing action '{action_name}': {e}\n{traceback.format_exc()}"

    def validate(self, full_block: str, command_name: str, args: list, content: str, lang) -> list:
        issues =[]
        if not args: return issues
        header = f"<@|{command_name} {' '.join(args)}"
        
        if not args[0].startswith('-') and len(args) > 1 and args[1].startswith('-'):
            corrected_args = [args[1], args[0]] + args[2:]
            corrected_header = f"<@|{command_name} {' '.join(corrected_args)}"
            issues.append({
                "original": full_block, "corrected": full_block.replace(header, corrected_header),
                "description": lang.get('correction_manage_order', "Flag should come before path."), "type": "syntax"
            })
            
        if args[0] in ('-move', '-copy'):
            if 'to' not in args:
                issues.append({
                    "original": full_block, "corrected": full_block,
                    "description": f"{args[0]} requires 'to' keyword (e.g. {args[0]} A to B).", "type": "syntax"
                })
        elif args[0] == '-rename':
            if 'as' not in args:
                issues.append({
                    "original": full_block, "corrected": full_block,
                    "description": "-rename requires 'as' keyword (e.g. -rename A as B).", "type": "syntax"
                })
                
        for arg in args:
            if not arg.startswith('-') and arg not in ('to', 'as') and not arg.startswith('<'):
                if not arg.startswith('@ROOT') and not arg.startswith('@APP-ROOT'):
                    corrected_arg = f"@ROOT/{arg}" if not arg.startswith('/') else f"@ROOT{arg}"
                    corrected_header = header.replace(arg, corrected_arg)
                    issues.append({
                        "original": full_block, "corrected": full_block.replace(header, corrected_header),
                        "description": f"Path '{arg}' should be prefixed with @ROOT/.", "type": "syntax"
                    })

        if args[0] == '-search':
            has_search_term = any(arg.startswith('<') and arg.endswith('>') for arg in args)
            if not has_search_term:
                corrected_header = f"{header} <keyword>"
                issues.append({
                    "original": full_block, "corrected": full_block.replace(header, corrected_header),
                    "description": lang.get('correction_manage_search_missing_keywords', "Missing search keyword in <...>"),
                    "type": "syntax"
                })
        return issues