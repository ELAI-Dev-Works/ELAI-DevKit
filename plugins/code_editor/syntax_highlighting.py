from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextFormat
from PySide6.QtCore import QRegularExpression

def create_format(color, style=''):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if 'bold' in style:
        fmt.setFontWeight(QFont.Weight.Bold)
    if 'italic' in style:
        fmt.setFontItalic(True)
    return fmt

class BaseHighlighter(QSyntaxHighlighter):
    """
    Base class for syntax highlighting. Extend this to add language-specific rules.
    Supports a proxy pattern for embedding highlighters within each other.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules =[]
        self._proxy = None
        self._sub_state = 0
        self._prev_sub_state = 0
        self.base_format = QTextCharFormat()

    @property
    def proxy(self):
        return self._proxy

    @proxy.setter
    def proxy(self, val):
        self._proxy = val

    def setFormat(self, start, length, fmt):
        if self._proxy:
            self._proxy.setFormat(start, length, fmt)
        else:
            merged = QTextCharFormat(fmt)
            if self.base_format.hasProperty(QTextFormat.BackgroundBrush):
                merged.setBackground(self.base_format.background())
            super().setFormat(start, length, merged)

    def do_set_current_block_state(self, state):
        self._sub_state = state
        if not self._proxy:
            self.setCurrentBlockState(state)

    def do_get_previous_block_state(self):
        if self._proxy:
            return self._prev_sub_state
        else:
            return self.previousBlockState()

    def add_rule(self, pattern, text_format):
        self.highlighting_rules.append((QRegularExpression(pattern), text_format))

    def highlightBlock(self, text):
        for pattern, text_format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), text_format)