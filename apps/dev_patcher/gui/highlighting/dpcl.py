from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QTextCharFormat
from plugins.code_editor.syntax_highlighting import BaseHighlighter, create_format
import re

class DPCLHighlighter(BaseHighlighter):
    """
    Syntax Highlighter for DPCL (DevPatch Commands Language).
    Dynamically loads and scopes language specific highlighters based on the DPCL context.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        from plugins.code_editor.highlighting import HighlighterManager
        self.subs = {
            1: HighlighterManager.get_highlighter('python'),
            2: HighlighterManager.get_highlighter('javascript'),
            3: HighlighterManager.get_highlighter('html'),
            4: HighlighterManager.get_highlighter('css'),
            5: HighlighterManager.get_highlighter('json')
        }
        for hl in self.subs.values():
            if hl: hl.proxy = self
            
        self.command_fmt = create_format("#C586C0", "bold")
        self.marker_fmt = create_format("#569CD6", "bold")
        self.variable_fmt = create_format("#4EC9B0", "bold")
        self.comment_fmt = create_format("#6A9955", "italic")
        self.arg_fmt = create_format("#DCDCAA")
        self.bracket_fmt = create_format("#CE9178")
        self.line_no_fmt = create_format("#858585")
        
        self.dpcl_rules = [
            (QRegularExpression(r"^[ \t]*-[a-zA-Z0-9_-]+"), self.arg_fmt),
            (QRegularExpression(r"(?<=\s)-[a-zA-Z0-9_-]+"), self.arg_fmt),
            (QRegularExpression(r"<[^>]*>"), self.bracket_fmt),
            (QRegularExpression(r"@[A-Z-]+"), self.variable_fmt),
            (QRegularExpression(r"^\s*\d+\s*\|"), self.line_no_fmt),
            (QRegularExpression(r"\{!RUN\}|\{!END\}"), self.command_fmt),
            (QRegularExpression(r"<@\|[A-Z]+"), self.command_fmt),
            (QRegularExpression(r"<-@.*?@->"), self.comment_fmt),
        ]

    def get_lang_id(self, ext):
        if ext in ('py', 'in'): return 1
        if ext in ('js', 'ts', 'jsx', 'tsx', 'node'): return 2
        if ext in ('html', 'htm', 'svg'): return 3
        if ext in ('css', 'scss', 'sass'): return 4
        if ext in ('json', 'json5'): return 5
        return 0
        
    def highlight_dpcl_line(self, text):
        for pattern, fmt in self.dpcl_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
                
    def highlight_inline_markers(self, text):
        pattern = re.compile(r"\{code_start\}|\{content\}|\{code_end\}|\{code_start\|content\|code_end\}")
        for match in pattern.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.marker_fmt)

    def highlightBlock(self, text):
        self.base_format.clearBackground()

        prev_state = self.previousBlockState()
        if prev_state == -1: prev_state = 0

        sub_state = prev_state & 0xFF
        lang_id = (prev_state >> 8) & 0xFF
        dpcl_ctx = (prev_state >> 16) & 0xFF

        self._prev_sub_state = sub_state
        self._sub_state = sub_state

        new_dpcl_ctx = dpcl_ctx
        new_lang_id = lang_id

        text_stripped = text.strip()

        if dpcl_ctx == 1:
            if text_stripped == "#@#":
                new_dpcl_ctx = 0
            self.setFormat(0, len(text), self.comment_fmt)
            self.setCurrentBlockState((new_dpcl_ctx << 16) | (new_lang_id << 8) | self._sub_state)
            return

        if text_stripped == "#@#":
            new_dpcl_ctx = 1
            self.setFormat(0, len(text), self.comment_fmt)
            self.setCurrentBlockState((new_dpcl_ctx << 16) | (new_lang_id << 8) | self._sub_state)
            return

        is_dpcl_line = False

        if re.match(r"^---[a-z_]+---$", text_stripped):
            self.setFormat(0, len(text), self.marker_fmt)
            is_dpcl_line = True
            if text_stripped == "---old---":
                new_dpcl_ctx = 2
                self._sub_state = 0
            elif text_stripped == "---new---":
                new_dpcl_ctx = 3
                self._sub_state = 0
            elif text_stripped in ("---content---", "---project---"):
                new_dpcl_ctx = 4
                self._sub_state = 0
            elif text_stripped in ("---end---", "---file_end---"):
                new_dpcl_ctx = 0
                self._sub_state = 0
            elif text_stripped == "---structure---":
                new_dpcl_ctx = 5
                self._sub_state = 0

        elif text_stripped.startswith("<###|"):
            self.setFormat(0, len(text), self.marker_fmt)
            is_dpcl_line = True
            new_dpcl_ctx = 4
            self._sub_state = 0
            ext_match = re.search(r'\.([a-zA-Z0-9_]+)(?:[\s>"\']|$)', text_stripped)
            if ext_match:
                new_lang_id = self.get_lang_id(ext_match.group(1).lower())

        elif text_stripped.startswith("<@|") or text_stripped.startswith("{!RUN}<@|"):
            is_dpcl_line = True
            new_dpcl_ctx = 0
            self._sub_state = 0
            ext_match = re.search(r'\.([a-zA-Z0-9_]+)(?:[\s>"\']|$)', text)
            if ext_match:
                new_lang_id = self.get_lang_id(ext_match.group(1).lower())
            self.highlight_dpcl_line(text)

        if not is_dpcl_line:
            if new_dpcl_ctx == 2:
                self.base_format.setBackground(QColor(220, 50, 50, 40))
                self.setFormat(0, len(text), self.base_format)
            elif new_dpcl_ctx == 3:
                self.base_format.setBackground(QColor(50, 220, 50, 40))
                self.setFormat(0, len(text), self.base_format)

            if new_dpcl_ctx in (2, 3, 4):
                if new_lang_id in self.subs and self.subs[new_lang_id]:
                    hl = self.subs[new_lang_id]
                    hl._prev_sub_state = self._prev_sub_state
                    hl._sub_state = self._sub_state
                    hl.highlightBlock(text)
                    self._sub_state = hl._sub_state
                self.highlight_inline_markers(text)
            elif new_dpcl_ctx == 0:
                self.highlight_dpcl_line(text)

        self.setCurrentBlockState((new_dpcl_ctx << 16) | (new_lang_id << 8) | self._sub_state)