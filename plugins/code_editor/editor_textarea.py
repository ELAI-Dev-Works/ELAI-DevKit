# This file contains the refactored CodeEditor class.
# It assembles the footer, settings panel, right panel, diff mixin, and line number area.

import re
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QPushButton, QFrame, QVBoxLayout, QCheckBox, QSpinBox, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, QRect, QVariantAnimation, QEasingCurve, QSize, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPalette, QTextFormat, QFont, QTextCursor

from .number_line import LineNumberArea
from .footer_panel import EditorFooter
from .settings_panel import EditorSettingsPanel
from .right_panel import RightPanel
from .diff import DiffMixin
from systems.gui.icons import IconManager

class CodeEditor(QPlainTextEdit, DiffMixin):
    diff_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_diff_data()  # from DiffMixin
        self.line_number_area = LineNumberArea(self)
        self.diff_lines = {}
        self.custom_line_numbers = {}
        self.command_order_map = {}

        self._parse_seq = 0

        self._parse_worker = None



        # Panels
        self.settings_panel = EditorSettingsPanel(self)
        self.footer = EditorFooter(self)
        self.right_panel = RightPanel(self)
        self.right_panel.diff_requested.connect(self.diff_requested.emit)
        self._right_panel_enabled = False
        self.right_panel.setVisible(False)

        # Animation for settings panel width change
        self.panel_closed_width = 30
        self.panel_open_width = 220
        self.current_panel_width = self.panel_closed_width
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(lambda val: self._on_panel_width_changed(val))

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.updateRequest.connect(lambda rect, dy: self.right_panel.update())
        self.cursorPositionChanged.connect(self.update_extra_selections)

        self.highlighter = None
        self._apply_font()
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        metrics = self.fontMetrics()
        self.setTabStopDistance(metrics.horizontalAdvance(' ') * 4)

        self.cursorPositionChanged.connect(self.footer.update_cursor)
        self.textChanged.connect(self.footer.update_stats)

        self.update_order_timer = QTimer(self)
        self.update_order_timer.setSingleShot(True)
        self.update_order_timer.setInterval(500)
        self.update_order_timer.timeout.connect(self._update_command_orders)
        self.textChanged.connect(self.update_order_timer.start)

        self.horizontalScrollBar().rangeChanged.connect(lambda min, max: self.update_margins_and_geometry())
        self.verticalScrollBar().rangeChanged.connect(lambda min, max: self.update_margins_and_geometry())

        self.update_margins_and_geometry()
        self.update_extra_selections()
        self.footer.update_stats()
        self.footer.update_cursor()
        self.update_order_timer.start(100)

    def set_right_panel_enabled(self, enabled: bool):
        self._right_panel_enabled = enabled
        self.right_panel.setVisible(enabled)
        self.update_margins_and_geometry()
        if enabled:
            self.right_panel.update()

    def right_panel_area_width(self):
        return 70 if self._right_panel_enabled else 0

    def keyPressEvent(self, event):
        if not self.isReadOnly():
            cursor = self.textCursor()
            if event.key() == Qt.Key_Tab and not cursor.hasSelection():
                self.insertPlainText("    ")
                return
            if event.key() == Qt.Key_Backspace and not cursor.hasSelection():
                pos = cursor.positionInBlock()
                text_before_cursor = cursor.block().text()[:pos]
                if text_before_cursor.strip() == "" and text_before_cursor.endswith("    "):
                    cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 4)
                    cursor.removeSelectedText()
                    return
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                cursor = self.textCursor()
                current_line = cursor.block().text()
                indentation = ""
                for char in current_line:
                    if char in (' ', '\t'):
                        indentation += char
                    else:
                        break
                super().keyPressEvent(event)
                if indentation:
                    self.insertPlainText(indentation)
                return
        super().keyPressEvent(event)

    def update_theme_colors(self, palette):
        self._last_palette = palette
        if hasattr(self.settings_panel, 'settings_btn'):
            icon_color = palette.get("icon_dim", "#858585")
            self.settings_panel.settings_btn.setIcon(IconManager.get_icon("core.wrench", icon_color))
        if hasattr(self.settings_panel, 'maximize_btn'):
            icon_color = palette.get("icon_dim", "#858585")
            self.settings_panel.maximize_btn.setIcon(IconManager.get_icon("core.maximize", icon_color))
        self.footer.update_theme_colors(palette)

    def open_maximized(self):
        from .maximize_window import MaximizedEditorDialog
        dialog = MaximizedEditorDialog(self, self.window())
        dialog.max_editor.settings_panel.maximize_btn.hide()  # optional: hide maximize in dialog
        dialog.exec()

    def toggle_word_wrap(self, state):
        if state == Qt.CheckState.Checked.value:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def change_font_size(self, size):
        font = self.font()
        if font.pointSize() != size:
            font.setPointSize(size)
            self.setFont(font)
            self.update_line_number_area_width(0)

    def _apply_font(self):
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.update_line_number_area_width(0)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.change_font_size(min(48, self.font().pointSize() + 1))
            elif delta < 0:
                self.change_font_size(max(6, self.font().pointSize() - 1))
            event.accept()
            return
        super().wheelEvent(event)

    def set_language(self, language: str):
        if hasattr(self, 'highlighter') and self.highlighter:
            self.highlighter.setDocument(None)
            self.highlighter = None
        if not language:
            return
        from plugins.code_editor.highlighting import HighlighterManager
        self.highlighter = HighlighterManager.get_highlighter(language, self.document())

    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 35 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _=0):
        self.update_margins_and_geometry()

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area_width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_margins_and_geometry()

    def _on_panel_width_changed(self, value):
        self.current_panel_width = value
        self.update_margins_and_geometry()

    def update_margins_and_geometry(self):
        cr = self.contentsRect()
        footer_height = self.footer.height()
        hbar = self.horizontalScrollBar()
        vbar = self.verticalScrollBar()
        hbar_h = hbar.height() if hbar.isVisible() else 0
        vbar_w = vbar.width() if vbar.isVisible() else 0

        left_width = self.current_panel_width + self.line_number_area_width()
        right_width = self.right_panel_area_width() if self._right_panel_enabled else 0
        self.setViewportMargins(left_width, 0, right_width, footer_height)

        # Position panels
        self.settings_panel.setGeometry(QRect(cr.left(), cr.top(), self.current_panel_width, cr.height()))
        self.settings_panel.update_geometry(cr)
        self.line_number_area.setGeometry(QRect(cr.left() + self.current_panel_width, cr.top(), self.line_number_area_width(), cr.height()))
        if self._right_panel_enabled:
            right_x = cr.left() + left_width + (cr.width() - left_width - right_width - vbar_w)
            self.right_panel.setGeometry(right_x, cr.top(), right_width, cr.height() - hbar_h)
        else:
            self.right_panel.setGeometry(0, 0, 0, 0)

        self.footer.setGeometry(QRect(cr.left() + left_width, cr.top() + cr.height() - footer_height - hbar_h, cr.width() - left_width - right_width, footer_height))

    def update_extra_selections(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(128, 128, 128, 40)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        # Diff highlights
        if hasattr(self, 'diff_lines') and self.diff_lines:
            doc = self.document()
            for block_num, marker in self.diff_lines.items():
                if marker in ('+', '-'):
                    selection = QTextEdit.ExtraSelection()
                    color = QColor(46, 204, 113, 40) if marker == '+' else QColor(231, 76, 60, 40)
                    selection.format.setBackground(color)
                    selection.format.setProperty(QTextFormat.FullWidthSelection, True)
                    selection.cursor = self.textCursor()
                    selection.cursor.setPosition(doc.findBlockByNumber(block_num).position())
                    selection.cursor.clearSelection()
                    extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        bg_color = self.palette().color(QPalette.ColorRole.Base).darker(105)
        painter.fillRect(event.rect(), bg_color)

        # Draw right-hand border for visual separation
        border_color = bg_color.lighter(180)
        area_width = self.line_number_area_width()
        painter.setPen(border_color)
        painter.drawLine(area_width - 1, event.rect().top(), area_width - 1, event.rect().bottom())

        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = round(self.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = ""
                if hasattr(self, 'custom_line_numbers') and block_number in self.custom_line_numbers:
                    number = self.custom_line_numbers[block_number]
                elif hasattr(self, 'diff_lines') and self.diff_lines and block_number in self.diff_lines and self.diff_lines[block_number] == '@':
                    number = ""
                elif hasattr(self, 'diff_lines') and self.diff_lines:
                    number = str(block_number + 1)
                else:
                    number = str(block_number + 1)

                if number:
                    painter.setPen(QColor("#858585"))
                    num_left = 20
                    num_width = self.line_number_area.width() - num_left - 5
                    painter.drawText(num_left, top, num_width, bottom - top,
                                     Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)

                # Diff markers (+/-) remain here
                if hasattr(self, 'diff_lines') and block_number in self.diff_lines:
                    marker = self.diff_lines[block_number]
                    if marker in ('+', '-'):
                        color = QColor("#a7ffa7") if marker == '+' else QColor("#ff9f9f")
                        painter.setPen(color)
                        painter.setFont(QFont("Consolas", 10, QFont.Bold))
                        marker_rect = QRect(5, top, 15, bottom - top)
                        painter.drawText(marker_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, marker)
                        painter.setFont(self.font())

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def _update_command_orders(self):
        self._parse_seq += 1
        seq = self._parse_seq
        text = self.toPlainText()

        def _parse_task():
            try:
                from apps.dev_patcher.core.command_planner import get_command_priority
            except ImportError:
                return {}

            commands =[]
            lines = text.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("<@|") or stripped.startswith("{!RUN}<@|"):
                    header = stripped.replace("{!RUN}<@|", "").replace("<@|", "")
                    parts = header.split()
                    if parts:
                        cmd_name = parts[0]
                        args = parts[1:]
                        priority = get_command_priority((cmd_name, args, ""), None)
                        commands.append({
                            'block_num': i,
                            'priority': priority,
                            'original_index': len(commands)
                        })
            commands.sort(key=lambda x: (x['priority'], x['original_index']))
            return {cmd['block_num']: order for order, cmd in enumerate(commands, start=1)}

        def _on_parsed(order_map):
            if seq == self._parse_seq:
                self.command_order_map = order_map
                self.line_number_area.update()
                self.right_panel.update()

        mw = self.window()
        tc = None
        if hasattr(mw, 'async_thread_manager'):
            tc = mw.async_thread_manager.thread
        elif hasattr(mw, 'main_window') and hasattr(mw.main_window, 'async_thread_manager'):
            tc = mw.main_window.async_thread_manager.thread

        if tc:
            self._parse_worker = tc.run_in_background(_parse_task, callback=_on_parsed, use_qt=True)
        else:
            _on_parsed(_parse_task())