from plugins.code_editor.syntax_highlighting import BaseHighlighter, create_format

class JSONHighlighter(BaseHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        key_fmt = create_format("#9CDCFE")
        string_fmt = create_format("#CE9178")
        number_fmt = create_format("#B5CEA8")
        bool_fmt = create_format("#569CD6", "bold")

        self.add_rule(r"\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b", number_fmt)
        self.add_rule(r"\b(true|false|null)\b", bool_fmt)
        self.add_rule(r'"[^"\\]*(\\.[^"\\]*)*"(?!\s*:)', string_fmt)
        self.add_rule(r'"[^"\\]*(\\.[^"\\]*)*"\s*:', key_fmt)