from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QFont

class RightPanel(QWidget):
    diff_requested = Signal(int)

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setMouseTracking(True)

    def sizeHint(self):
        return QSize(self.editor.right_panel_area_width(), 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        bg_color = self.editor.palette().color(self.editor.backgroundRole()).darker(105)
        painter.fillRect(event.rect(), bg_color)
        # Draw left-hand border for visual separation
        border_color = bg_color.lighter(180)
        painter.setPen(border_color)
        painter.drawLine(0, event.rect().top(), 0, event.rect().bottom())

        if not hasattr(self.editor, 'command_order_map') or not self.editor.command_order_map:
            return

        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.editor.contentOffset()
        top = round(self.editor.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())

        # Dimensions
        area_width = self.editor.right_panel_area_width()
        diff_btn_width = 32
        order_width = 26
        spacing = 4

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                text_stripped = block.text().strip()
                is_diff_cmd = False
                if text_stripped.startswith("<@|EDIT") or text_stripped.startswith("{!RUN}<@|EDIT"):
                    is_diff_cmd = True
                elif text_stripped.startswith("<@|REFACTOR") or text_stripped.startswith("{!RUN}<@|REFACTOR"):
                    is_diff_cmd = True
                elif (text_stripped.startswith("<@|MANAGE") or text_stripped.startswith("{!RUN}<@|MANAGE")) and "-write" in text_stripped:
                    is_diff_cmd = True

                # Draw Command Order (if present)
                if block_number in self.editor.command_order_map:
                    order = self.editor.command_order_map[block_number]
                    order_rect = QRect(spacing, top + 2, order_width, bottom - top - 4)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor("#a855f7"))
                    painter.drawRoundedRect(order_rect, 3, 3)
                    painter.setPen(QColor("white"))
                    painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
                    painter.drawText(order_rect, Qt.AlignCenter, f"#{order}")
                    painter.setFont(self.editor.font())

                # Draw DIFF button (if applicable)
                if is_diff_cmd:
                    diff_rect = QRect(spacing + order_width + 2, top + 2, diff_btn_width, bottom - top - 4)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor("#0ea5e9"))
                    painter.drawRoundedRect(diff_rect, 4, 4)
                    painter.setPen(QColor("white"))
                    painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
                    painter.drawText(diff_rect, Qt.AlignCenter, "DIFF")
                    painter.setFont(self.editor.font())

            block = block.next()
            top = bottom
            bottom = top + round(self.editor.blockBoundingRect(block).height())
            block_number += 1

    def mousePressEvent(self, event):
        pos = event.pos()
        area_width = self.editor.right_panel_area_width()
        diff_btn_left = self.editor.line_number_area_width() - 35  # approximate offset from left; we need relative positions
        # Actually, we need to compute coordinates based on block positions using the same logic as paintEvent.
        # We'll iterate similarly to find which block was clicked.
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.editor.contentOffset()
        top = round(self.editor.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + round(self.editor.blockBoundingRect(block).height())
        spacing = 4
        order_width = 26
        diff_btn_width = 32
        diff_left = spacing + order_width + 2

        while block.isValid() and top <= pos.y():
            if block.isVisible():
                text_stripped = block.text().strip()
                is_diff_cmd = False
                if text_stripped.startswith("<@|EDIT") or text_stripped.startswith("{!RUN}<@|EDIT"):
                    is_diff_cmd = True
                elif text_stripped.startswith("<@|REFACTOR") or text_stripped.startswith("{!RUN}<@|REFACTOR"):
                    is_diff_cmd = True
                elif (text_stripped.startswith("<@|MANAGE") or text_stripped.startswith("{!RUN}<@|MANAGE")) and "-write" in text_stripped:
                    is_diff_cmd = True

                if is_diff_cmd and pos.x() >= diff_left and pos.x() <= diff_left + diff_btn_width and top <= pos.y() <= bottom:
                    self.diff_requested.emit(block_number)
                    return
            block = block.next()
            top = bottom
            bottom = top + round(self.editor.blockBoundingRect(block).height())
            block_number += 1

        super().mousePressEvent(event)