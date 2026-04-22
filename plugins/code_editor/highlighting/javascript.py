from plugins.code_editor.syntax_highlighting import BaseHighlighter, create_format

class JavascriptHighlighter(BaseHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        keyword_fmt = create_format("#569CD6", "bold")
        flow_fmt = create_format("#C586C0", "bold")
        string_fmt = create_format("#CE9178")
        number_fmt = create_format("#B5CEA8")
        comment_fmt = create_format("#6A9955", "italic")
        func_fmt = create_format("#DCDCAA")

        keywords =["class", "const", "debugger", "delete", "export", "extends", "function", "import", "in", "instanceof", "new", "super", "this", "typeof", "var", "void", "let", "await", "async"]
        flow =["break", "case", "catch", "continue", "default", "do", "else", "finally", "for", "if", "return", "switch", "throw", "try", "while", "with", "yield"]

        self.add_rule(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()", func_fmt)

        for word in keywords:
            self.add_rule(rf"\b{word}\b", keyword_fmt)
        for word in flow:
            self.add_rule(rf"\b{word}\b", flow_fmt)

        self.add_rule(r"\b(true|false|null|undefined)\b", keyword_fmt)
        self.add_rule(r"\b[0-9]+(\.[0-9]+)?\b", number_fmt)

        self.add_rule(r'"[^"\\]*(\\.[^"\\]*)*"', string_fmt)
        self.add_rule(r"'[^'\\]*(\\.[^'\\]*)*'", string_fmt)
        self.add_rule(r"`[^`\\]*(\\.[^`\\]*)*`", string_fmt)

        self.add_rule(r"//[^\n]*", comment_fmt)

        self.multi_comment_fmt = comment_fmt

    def highlightBlock(self, text):
        super().highlightBlock(text)
        self.do_set_current_block_state(0)
        start_index = 0
        if self.do_get_previous_block_state() != 1:
            start_index = text.find("/*")

        while start_index >= 0:
            end_index = text.find("*/", start_index + 2)
            if end_index == -1:
                self.do_set_current_block_state(1)
                self.setFormat(start_index, len(text) - start_index, self.multi_comment_fmt)
                break
            else:
                self.setFormat(start_index, end_index - start_index + 2, self.multi_comment_fmt)
                start_index = text.find("/*", end_index + 2)