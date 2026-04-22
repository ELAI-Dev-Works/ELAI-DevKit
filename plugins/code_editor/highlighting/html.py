from plugins.code_editor.syntax_highlighting import BaseHighlighter, create_format

class HTMLHighlighter(BaseHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        tag_fmt = create_format("#569CD6")
        attr_fmt = create_format("#9CDCFE")
        string_fmt = create_format("#CE9178")
        self.comment_fmt = create_format("#6A9955", "italic")

        self.add_rule(r"</?[a-zA-Z0-9\-]+", tag_fmt)
        self.add_rule(r">", tag_fmt)
        self.add_rule(r"\b[a-zA-Z\-:]+(?=\s*=)", attr_fmt)
        self.add_rule(r'"[^"]*"', string_fmt)
        self.add_rule(r"'[^']*'", string_fmt)

        from plugins.code_editor.highlighting import HighlighterManager
        self.js_hl = HighlighterManager.get_highlighter('javascript')
        if self.js_hl: self.js_hl.proxy = self
        self.css_hl = HighlighterManager.get_highlighter('css')
        if self.css_hl: self.css_hl.proxy = self

    def highlightBlock(self, text):
        state = self.do_get_previous_block_state()
        if state == -1: state = 0
        
        html_state = state & 0x0F
        inner_state = (state >> 4) & 0x0F
        
        if self.js_hl:
            self.js_hl._prev_sub_state = inner_state
            self.js_hl._sub_state = inner_state
        if self.css_hl:
            self.css_hl._prev_sub_state = inner_state
            self.css_hl._sub_state = inner_state
        
        if html_state == 0 or html_state == 1:
            super().highlightBlock(text)
            self.do_set_current_block_state(0)
            
            start_index = 0
            if html_state != 1:
                start_index = text.find("<!--")
                
            while start_index >= 0:
                end_index = text.find("-->", start_index + 4)
                if end_index == -1:
                    self.do_set_current_block_state(1)
                    self.setFormat(start_index, len(text) - start_index, self.comment_fmt)
                    break
                else:
                    self.setFormat(start_index, end_index - start_index + 3, self.comment_fmt)
                    start_index = text.find("<!--", end_index + 3)
                    
            if self._sub_state != 1:
                if "<script" in text and "</script>" not in text:
                    html_state = 2
                    inner_state = 0
                elif "<style" in text and "</style>" not in text:
                    html_state = 3
                    inner_state = 0
                    
        elif html_state == 2:
            idx = text.find("</script>")
            if idx >= 0:
                if self.js_hl:
                    self.js_hl.highlightBlock(text[:idx])
                html_state = 0
                inner_state = 0
                super().highlightBlock(text)
            else:
                if self.js_hl:
                    self.js_hl.highlightBlock(text)
                    inner_state = self.js_hl._sub_state

        elif html_state == 3:
            idx = text.find("</style>")
            if idx >= 0:
                if self.css_hl:
                    self.css_hl.highlightBlock(text[:idx])
                html_state = 0
                inner_state = 0
                super().highlightBlock(text)
            else:
                if self.css_hl:
                    self.css_hl.highlightBlock(text)
                    inner_state = self.css_hl._sub_state

        self.do_set_current_block_state((inner_state << 4) | html_state)