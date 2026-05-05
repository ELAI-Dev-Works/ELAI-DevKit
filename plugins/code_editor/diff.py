import re

class DiffMixin:
    """Mixin providing diff-related functionality."""

    def _init_diff_data(self):
        self.diff_lines = {}
        self.custom_line_numbers = {}

    def set_diff_text(self, diff_text):
        self.clear()
        self.setReadOnly(True)
        if not hasattr(self, 'diff_lines'):
            self._init_diff_data()
        self.diff_lines = {}
        self.custom_line_numbers = {}

        lines = diff_text.splitlines()
        clean_lines = []

        h_pattern = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
        current_old = 1
        current_new = 1
        in_hunk = False

        for line in lines:
            line_idx = len(clean_lines)

            if line.startswith('+++') or line.startswith('---'):
                continue

            if line.startswith('@@'):
                match = h_pattern.search(line)
                if match:
                    current_old = int(match.group(1))
                    current_new = int(match.group(2))
                    in_hunk = True
                self.diff_lines[line_idx] = '@'
                clean_lines.append(line)
            elif in_hunk:
                if line.startswith('+'):
                    self.diff_lines[line_idx] = '+'
                    self.custom_line_numbers[line_idx] = str(current_new)
                    clean_lines.append(line[1:])
                    current_new += 1
                elif line.startswith('-'):
                    self.diff_lines[line_idx] = '-'
                    self.custom_line_numbers[line_idx] = str(current_old)
                    clean_lines.append(line[1:])
                    current_old += 1
                elif line.startswith(' '):
                    self.custom_line_numbers[line_idx] = str(current_new)
                    clean_lines.append(line[1:])
                    current_old += 1
                    current_new += 1
                elif line == '':
                    self.custom_line_numbers[line_idx] = str(current_new)
                    clean_lines.append("")
                    current_old += 1
                    current_new += 1
                else:
                    clean_lines.append(line)
            else:
                clean_lines.append(line)

        self.setPlainText('\n'.join(clean_lines))
        self.update_extra_selections()