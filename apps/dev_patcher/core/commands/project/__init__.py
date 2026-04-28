from typing import Tuple
from .. import BaseCommand

class Command(BaseCommand):
    
    PRIORITY = 1

    def build_backup(self, args: list, content: str, project_root: str, backup_builder):
        if "---project---" in content:
            files = content.split("---project---", 1)[1]
            file_blocks = files.split("<###|")[1:]
            for block in file_blocks:
                parts = block.split('\n', 1)
                filepath = parts[0].strip()
                if filepath.endswith('>'): filepath = filepath[:-1]
                backup_builder.use("delete", filepath)

        if '-python' in args:
            backup_builder.use("delete", "requirements.in")
            backup_builder.use("delete", "setup_run(uv).bat")
            backup_builder.use("delete", "run(pip).bat")
            backup_builder.use("delete", "setup_run(uv).sh")
            backup_builder.use("delete", "run(pip).sh")
        if '-nodejs' in args:
            backup_builder.use("delete", "package.json")
            backup_builder.use("delete", "run(nodejs).bat")
            backup_builder.use("delete", "run(nodejs).sh")
        if '-web' in args:
            backup_builder.use("delete", "index.html")
            backup_builder.use("delete", "server.bat")
            backup_builder.use("delete", "server.sh")
            backup_builder.use("delete", "simple_server.js")

        for arg in args:
            if arg.startswith('<') and arg.endswith('>') and args.index(arg) > 0 and args[args.index(arg)-1] == '-run':
                backup_builder.use("delete", arg[1:-1])

    
    def execute(self, args: list, content: str, fs_handler) -> Tuple[bool, str]:
        if not args or '-setup' not in args:
            return False, "The PROJECT command requires a primary argument -setup."

        action_name = 'setup'

        try:
            action_module = self._load_action_module("project", action_name, __package__, fs_handler.root)
            if action_module:
                return action_module.run(args, content, fs_handler)
            else:
                return False, f"Failed to load module for PROJECT command: {action_name}"
        except Exception as e:
            import traceback
            return False, f"Error executing action '{action_name}': {e}\n{traceback.format_exc()}"


    def validate(self, full_block: str, command_name: str, args: list, content: str, lang) -> list:
        issues =[]
        header = f"<@|{command_name} {' '.join(args)}"
        def find_arg_value(arg_name, args_list):
            try:
                if arg_name not in args_list: return None
                start_index = args_list.index(arg_name) + 1
                if start_index >= len(args_list): return None
                if args_list[start_index].startswith('<') and args_list[start_index].endswith('>'):
                    return args_list[start_index]
                if args_list[start_index].startswith('<'):
                    value_parts =[]
                    for i in range(start_index, len(args_list)):
                        part = args_list[i]
                        value_parts.append(part)
                        if part.endswith('>'): return " ".join(value_parts)
                return None
            except ValueError:
                return None

        if not find_arg_value('-run', args):
            issues.append({
                "original": full_block, "corrected": full_block.replace(header, f"{header} -run <main.py>"),
                "description": lang.get('correction_project_missing_run'), "type": "syntax"
            })
        if not find_arg_value('-requi', args):
            issues.append({
                "original": full_block, "corrected": full_block.replace(header, f"{header} -requi <None>"),
                "description": lang.get('correction_project_missing_requi'), "type": "syntax"
            })
        if '-name' in args:
            val = find_arg_value('-name', args)
            if not val:
                name_index = args.index("-name")
                token_to_replace = ' '.join(args[name_index+1:]) if name_index + 1 < len(args) else ""
                issues.append({
                    "original": full_block, "corrected": full_block,
                    "description": lang.get('correction_project_missing_name'), "type": "interactive",
                    "input_request": {
                        "label": "Enter a project name. For names with spaces, use <(Project Name)>:",
                        "token_to_replace": token_to_replace
                    }
                })
            else:
                inner = val[1:-1]
                if ' ' in inner and not (inner.startswith('(') and inner.endswith(')')):
                    corrected_val = f"<({inner})>"
                    issues.append({
                        "original": full_block, "corrected": full_block.replace(val, corrected_val),
                        "description": "The -name argument contains spaces but is not wrapped in parentheses. The new format is <(Name With Spaces)>.",
                        "type": "syntax"
                    })
        return issues

