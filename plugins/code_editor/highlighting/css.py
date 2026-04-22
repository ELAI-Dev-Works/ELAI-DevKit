from plugins.code_editor.syntax_highlighting import BaseHighlighter, create_format

class CSSHighlighter(BaseHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        selector_fmt = create_format("#D7BA7D")
        prop_fmt = create_format("#9CDCFE")
        val_fmt = create_format("#CE9178")
        number_fmt = create_format("#B5CEA8")
        comment_fmt = create_format("#6A9955", "italic")
        pseudo_fmt = create_format("#C586C0")

        self.add_rule(r"\b[a-zA-Z\-]+\s*:", prop_fmt)
        self.add_rule(r"#[a-zA-Z0-9_-]+", selector_fmt)
        self.add_rule(r"\.[a-zA-Z0-9_-]+", selector_fmt)
        self.add_rule(r"\b[0-9]+(px|em|rem|%|vh|vw|s|ms)?\b", number_fmt)
        self.add_rule(r"::[a-zA-Z0-9_-]+", pseudo_fmt)
        self.add_rule(r":[a-zA-Z0-9_-]+", pseudo_fmt)
        self.add_rule(r'"[^"]*"', val_fmt)
        self.add_rule(r"'[^']*'", val_fmt)

        self.comment_fmt = comment_fmt

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
                self.setFormat(start_index, len(text) - start_index, self.comment_fmt)
                break
            else:
                self.setFormat(start_index, end_index - start_index + 2, self.comment_fmt)
                start_index = text.find("/*", end_index + 2)