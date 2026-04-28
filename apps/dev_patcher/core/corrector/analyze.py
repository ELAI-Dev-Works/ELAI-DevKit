from .syntax_validator import SyntaxValidator
from .command_validator import CommandValidator

class Analyzer:
    """
    Orchestrates different validation passes over the patch content.
    """
    def __init__(self, patch_text: str, flags: dict, lang):
        self.patch_text = patch_text
        self.flags = flags
        self.lang = lang

    def run(self):
        issues =[]
        
        # 1. Structural and Syntax Validation
        syntax_val = SyntaxValidator(self.patch_text, self.flags, self.lang)
        issues.extend(syntax_val.validate())

        # 2. Command-Specific Logical Validation
        cmd_val = CommandValidator(self.patch_text, self.lang)
        issues.extend(cmd_val.validate())

        return issues