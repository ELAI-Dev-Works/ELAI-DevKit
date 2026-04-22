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