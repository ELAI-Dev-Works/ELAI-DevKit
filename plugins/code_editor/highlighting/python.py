from PySide6.QtCore import QRegularExpression
from plugins.code_editor.syntax_highlighting import BaseHighlighter, create_format

class PythonHighlighter(BaseHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        keyword_fmt = create_format("#C586C0", "bold")
        builtin_fmt = create_format("#569CD6")
        string_fmt = create_format("#CE9178")
        number_fmt = create_format("#B5CEA8")
        comment_fmt = create_format("#6A9955", "italic")
        decorator_fmt = create_format("#DCDCAA", "italic")

        keywords =[
            "and", "as", "assert", "async", "await", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "finally", "for", "from", "global", "if",
            "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise",
            "return", "try", "while", "with", "yield"
        ]
        builtins =["True", "False", "None"]

        for word in keywords:
            self.add_rule(rf"\b{word}\b", keyword_fmt)
        for word in builtins:
            self.add_rule(rf"\b{word}\b", builtin_fmt)

        func_fmt = create_format("#DCDCAA")

        self.add_rule(r"@[a-zA-Z_][a-zA-Z0-9_.]*", decorator_fmt)
        self.add_rule(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()", func_fmt)

        for word in keywords:
            self.add_rule(rf"\b{word}\b", keyword_fmt)
        for word in builtins:
            self.add_rule(rf"\b{word}\b", builtin_fmt)

        self.add_rule(r"\b[0-9]+(\.[0-9]+)?\b", number_fmt)

        self.add_rule(r'"[^"\\]*(\\.[^"\\]*)*"', string_fmt)
        self.add_rule(r"'[^'\\]*(\\.[^'\\]*)*'", string_fmt)
        self.add_rule(r"#[^\n]*", comment_fmt)

        self.multi_line_string_fmt = string_fmt

    def highlightBlock(self, text):
        super().highlightBlock(text)
        self.do_set_current_block_state(0)

        start_index = 0
        state = self.do_get_previous_block_state()

        if state != 1 and state != 2:
            idx1 = text.find('"""')
            idx2 = text.find("'''")
            if idx1 >= 0 and idx2 >= 0:
                if idx1 < idx2:
                    start_index = idx1
                    state = 1
                else:
                    start_index = idx2
                    state = 2
            elif idx1 >= 0:
                start_index = idx1
                state = 1
            elif idx2 >= 0:
                start_index = idx2
                state = 2
            else:
                start_index = -1
                state = -1
        else:
            start_index = 0

        while start_index >= 0:
            marker = '"""' if state == 1 else "'''"
            search_offset = start_index + 3 if (self.do_get_previous_block_state() not in (1, 2) or start_index > 0) else 0
            end_index = text.find(marker, search_offset)

            if end_index == -1:
                self.do_set_current_block_state(state)
                self.setFormat(start_index, len(text) - start_index, self.multi_line_string_fmt)
                break
            else:
                self.setFormat(start_index, end_index - start_index + 3, self.multi_line_string_fmt)

                idx1 = text.find('"""', end_index + 3)
                idx2 = text.find("'''", end_index + 3)
                if idx1 >= 0 and idx2 >= 0:
                    if idx1 < idx2:
                        start_index = idx1
                        state = 1
                    else:
                        start_index = idx2
                        state = 2
                elif idx1 >= 0:
                    start_index = idx1
                    state = 1
                elif idx2 >= 0:
                    start_index = idx2
                    state = 2
                else:
                    start_index = -1
                    state = -1