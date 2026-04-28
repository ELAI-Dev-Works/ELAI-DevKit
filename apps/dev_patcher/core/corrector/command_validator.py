import re
import importlib
from apps.dev_patcher.core.custom_loader import CustomCommandLoader

class CommandValidator:
    """
    Parses valid command blocks and delegates validation logic to the specific command class.
    """
    def __init__(self, patch_text: str, lang):
        self.patch_text = patch_text
        self.lang = lang

    def validate(self):
        issues =[]
        command_blocks = re.finditer(r"(<@\|.*?---end---)", self.patch_text, re.DOTALL)

        for block_match in command_blocks:
            full_block = block_match.group(1)
            start_line = self.patch_text[:block_match.start()].count('\n') + 1

            header_match = re.search(r"<@\|(.*?)\n", full_block)
            if not header_match: 
                continue

            header = header_match.group(1).strip()
            parts = header.split()
            if not parts:
                continue
                
            command_name = parts[0].upper()
            args = parts[1:]
            content = full_block.split('\n', 1)[1].rsplit('---end---', 1)[0]

            cmd_issues = self._validate_command(command_name, full_block, args, content)
            for issue in cmd_issues:
                if "start_line" not in issue:
                    issue["start_line"] = start_line
                issues.append(issue)

        return issues

    def _validate_command(self, command_name, full_block, args, content):
        try:
            # 1. Try standard commands
            module_name = f"apps.dev_patcher.core.commands.{command_name.lower()}"
            tool_module = importlib.import_module(module_name)
            tool_instance = tool_module.Command()
            if hasattr(tool_instance, 'validate'):
                return tool_instance.validate(full_block, command_name, args, content, self.lang)
        except ImportError:
            # 2. Try custom commands (assuming context handles this implicitly or fails gracefully)
            pass
        except Exception:
            pass
        return[]