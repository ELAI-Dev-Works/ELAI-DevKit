import importlib
from typing import Tuple
from .. import BaseCommand

class Command(BaseCommand):
    """
    Performs smart code refactoring using AST analysis.
    """
    PRIORITY = 10 

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
            action_module = self._load_action_module("refactor", action_name, __package__, fs_handler.root)
            if action_module:
                return action_module.run(args, content, fs_handler)
            else:
                return False, f"Unknown argument for REFACTOR command: {action_arg}"
        except Exception as e:
            import traceback
            return False, f"Error executing refactor action '{action_name}': {e}\n{traceback.format_exc()}"

    def validate(self, full_block: str, command_name: str, args: list, content: str, lang) -> list:
        issues =[]
        header = f"<@|{command_name} {' '.join(args)}"
        
        if not args:
            issues.append({
                "original": full_block, "corrected": full_block,
                "description": "REFACTOR requires an action flag (-rename, -inject, -imports).", "type": "syntax"
            })
            return issues
            
        action = args[0]
        
        if action == '-rename':
            if 'to' not in args:
                issues.append({
                    "original": full_block, "corrected": full_block,
                    "description": "-rename requires 'to' keyword.", "type": "syntax"
                })
            if '-project' not in args and "---files---" not in content:
                corrected_content = f"---files---\n@ROOT/path/to/file.py\n---\n{content}"
                issues.append({
                    "original": full_block, "corrected": full_block.replace(content, corrected_content),
                    "description": "Missing '---files---' block or '-project' flag.", "type": "syntax"
                })
                
        elif action == '-inject':
            if '-pos' not in args:
                issues.append({
                    "original": full_block, "corrected": full_block.replace(header, f"{header} -pos <end>"),
                    "description": "-inject requires '-pos <...>' argument.", "type": "syntax"
                })
            if "---content---" not in content:
                corrected_content = f"{content}\n---content---\n# injected code here"
                issues.append({
                    "original": full_block, "corrected": full_block.replace(content, corrected_content),
                    "description": "-inject requires '---content---' block.", "type": "syntax"
                })
                
        return issues