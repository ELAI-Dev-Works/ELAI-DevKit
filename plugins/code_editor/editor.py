from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QPushButton, QFrame, QVBoxLayout, QCheckBox, QSpinBox, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, QRect, QVariantAnimation, QEasingCurve, QSize, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPalette, QTextFormat, QFont
from .number_line import LineNumberArea
from assets.icons import svg_to_icon, get_svg_content, ICON_WRENCH

class CodeEditor(QPlainTextEdit):
    """
    A fully-featured code editor widget replacing QTextEdit, with line numbers and syntax highlighting support.
    """
    diff_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        # Animation configuration
        self.panel_closed_width = 30
        self.panel_open_width = 220
        self.current_panel_width = self.panel_closed_width
        self.is_panel_open = False

        self.animation = QVariantAnimation(self)
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self._on_panel_width_changed)

        # Settings Panel
        self.settings_panel = QFrame(self)
        self.settings_panel.setObjectName("EditorSettingsPanel")
        self.settings_panel.setStyleSheet("""
            #EditorSettingsPanel {
                border-right: 1px solid rgba(128, 128, 128, 0.3);
            }
        """)

        # Settings Toggle Button (Inside panel, always visible)
        self.settings_btn = QPushButton(self.settings_panel)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setIcon(svg_to_icon(get_svg_content(ICON_WRENCH), "#858585"))
        self.settings_btn.setIconSize(QSize(18, 18))
        self.settings_btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; margin: 4px; }
            QPushButton:hover { background-color: rgba(128, 128, 128, 0.2); }
        """)
        self.settings_btn.clicked.connect(self.toggle_settings_panel)

        # Settings Content Container (Inside panel, clipped when closed)
        self.settings_content = QWidget(self.settings_panel)
        content_layout = QVBoxLayout(self.settings_content)
        content_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel("Editor Settings")
        title_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(title_label)

        self.wrap_checkbox = QCheckBox("Word Wrap")
        self.wrap_checkbox.stateChanged.connect(self.toggle_word_wrap)
        content_layout.addWidget(self.wrap_checkbox)

        font_layout = QHBoxLayout()
        font_label = QLabel("Font Size:")
        self.font_spinbox = QSpinBox()
        self.font_spinbox.setRange(6, 48)
        self.font_spinbox.setValue(10)
        self.font_spinbox.valueChanged.connect(self.change_font_size)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_spinbox)
        content_layout.addLayout(font_layout)

        content_layout.addStretch()

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.highlighter = None

        self._apply_font()
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.update_margins_and_geometry()
        self.highlight_current_line()

    def update_theme_colors(self, palette):
        if hasattr(self, 'settings_btn'):
            icon_color = palette.get("icon_dim", "#858585")
            self.settings_btn.setIcon(svg_to_icon(get_svg_content(ICON_WRENCH), icon_color))

    def toggle_settings_panel(self):
        self.is_panel_open = not self.is_panel_open
        start_val = self.current_panel_width
        end_val = self.panel_open_width if self.is_panel_open else self.panel_closed_width

        self.animation.stop()
        self.animation.setStartValue(start_val)
        self.animation.setEndValue(end_val)
        self.animation.start()

    def _on_panel_width_changed(self, value):
        self.current_panel_width = value
        self.update_margins_and_geometry()

    def update_margins_and_geometry(self):
        cr = self.contentsRect()
        self.settings_panel.setGeometry(QRect(cr.left(), cr.top(), self.current_panel_width, cr.height()))
        self.settings_btn.setGeometry(QRect(0, 0, self.panel_closed_width, 30))
        self.settings_content.setGeometry(QRect(self.panel_closed_width, 0, self.panel_open_width - self.panel_closed_width, cr.height()))
        self.line_number_area.setGeometry(QRect(cr.left() + self.current_panel_width, cr.top(), self.line_number_area_width(), cr.height()))
        self.setViewportMargins(self.current_panel_width + self.line_number_area_width(), 0, 0, 0)

    def toggle_word_wrap(self, state):
        if state == Qt.CheckState.Checked.value:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def change_font_size(self, size):
        if self.font_spinbox.value() != size:
            self.font_spinbox.setValue(size)
        self._apply_font()

    def _apply_font(self):
        font = QFont("Consolas", self.font_spinbox.value())
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.update_line_number_area_width(0)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.change_font_size(min(self.font_spinbox.maximum(), self.font_spinbox.value() + 1))
            elif delta < 0:
                self.change_font_size(max(self.font_spinbox.minimum(), self.font_spinbox.value() - 1))
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
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        space += 38 # Space for DIFF button
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

    def highlight_current_line(self):
        extra_selections =[]
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(128, 128, 128, 40)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
    
        bg_color = self.palette().color(QPalette.ColorRole.Base).darker(105)
        painter.fillRect(event.rect(), bg_color)
    
        painter.setFont(self.font())
    
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = round(self.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + round(self.blockBoundingRect(block).height())
    
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(0, top, self.line_number_area.width() - 40, round(self.blockBoundingRect(block).height()),
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)
    
                text_stripped = block.text().strip()
                if text_stripped.startswith("<@|EDIT") or text_stripped.startswith("{!RUN}<@|EDIT"):
                    diff_rect = QRect(self.line_number_area.width() - 35, top + 2, 32, round(self.blockBoundingRect(block).height()) - 4)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor("#0ea5e9"))
                    painter.drawRoundedRect(diff_rect, 4, 4)
                    painter.setPen(QColor("white"))
                    painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
                    painter.drawText(diff_rect, Qt.AlignmentFlag.AlignCenter, "DIFF")
                    painter.setFont(self.font()) # RESTORE
    
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
    
    def lineNumberAreaMousePressEvent(self, event):
        if event.pos().x() >= self.line_number_area.width() - 40:
            cursor = self.cursorForPosition(QPoint(0, event.pos().y()))
            block = cursor.block()
            text_stripped = block.text().strip()
            if text_stripped.startswith("<@|EDIT") or text_stripped.startswith("{!RUN}<@|EDIT"):
                self.diff_requested.emit(block.blockNumber())