import re
from .syntax.command import check_command_syntax
from .syntax.comments import check_comments_syntax
from .syntax.raw_blocks import check_raw_blocks_syntax
from .syntax.end import check_end_syntax

class SyntaxValidator:
    """
    Validates global markers, missing features, and basic syntax rules.
    """
    def __init__(self, patch_text: str, flags: dict, lang):
        self.patch_text = patch_text
        self.flags = flags
        self.lang = lang

    def validate(self):
        issues =[]
        lines = self.patch_text.splitlines()

        # Check for misplaced markers that have leading whitespace
        marker_pattern = re.compile(r"^(\s+)(---(?:old|new|end|scope|structure|project|file_end)---)")
        for i, line in enumerate(lines):
            match = marker_pattern.match(line)
            if match:
                whitespace, marker = match.groups()
                issues.append({
                    "original": line,
                    "corrected": marker,
                    "description": self.lang.get('correction_whitespace_marker'),
                    "type": "syntax",
                    "start_line": i + 1
                })

        # Feature suggestions checking
        if "---scope---" in self.patch_text and not self.flags.get('scope'):
            issues.append({
                "original": "---scope---",
                "corrected": "---scope---",
                "description": self.lang.get('correction_enable_scope'),
                "type": "suggestion",
                "feature": "scope"
            })

        if re.search(r"^\s*\d+\s*\|", self.patch_text, re.MULTILINE) and not self.flags.get('lineno'):
            issues.append({
                "original": "e.g., '12| code'",
                "corrected": "e.g., '12| code'",
                "description": self.lang.get('correction_enable_lineno'),
                "type": "suggestion",
                "feature": "lineno"
            })

        # Sub-modules checks
        issues.extend(check_command_syntax(lines, self.lang))
        issues.extend(check_comments_syntax(lines, self.lang))
        issues.extend(check_raw_blocks_syntax(lines, self.lang))
        issues.extend(check_end_syntax(lines, self.lang))

        return issues