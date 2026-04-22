from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QSize

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

    def mousePressEvent(self, event):
        if hasattr(self.editor, 'lineNumberAreaMousePressEvent'):
            self.editor.lineNumberAreaMousePressEvent(event)
        super().mousePressEvent(event)
