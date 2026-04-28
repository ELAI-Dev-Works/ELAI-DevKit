from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QPushButton, QFrame, QVBoxLayout, QCheckBox, QSpinBox, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, QRect, QVariantAnimation, QEasingCurve, QSize, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPalette, QTextFormat, QFont, QTextCursor
from .number_line import LineNumberArea
from systems.gui.icons import svg_to_icon, get_svg_content, ICON_WRENCH

class CodeEditor(QPlainTextEdit):
    """
    A fully-featured code editor widget replacing QTextEdit, with line numbers and syntax highlighting support.
    """
    diff_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.diff_lines = {}  # Store diff markers (+, -, @, H) for line blocks

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
        self.setMinimumHeight(50)

        # Fix tab width visually (4 spaces equivalent)
        metrics = self.fontMetrics()
        self.setTabStopDistance(metrics.horizontalAdvance(' ') * 4)

        self.update_margins_and_geometry()
        self.highlight_current_line()

    def keyPressEvent(self, event):
        if not self.isReadOnly():
            cursor = self.textCursor()

            # 1. Fix Tab indentation (force 4 spaces)
            if event.key() == Qt.Key_Tab and not cursor.hasSelection():
                self.insertPlainText("    ")
                return

            # Smart Backspace for un-indenting
            if event.key() == Qt.Key_Backspace and not cursor.hasSelection():
                pos = cursor.positionInBlock()
                text_before_cursor = cursor.block().text()[:pos]
                # If cursor is inside indentation (text to the left is all whitespace)
                if text_before_cursor.strip() == "":
                    # If the text to the left ends with 4 spaces, delete a "tab"
                    if text_before_cursor.endswith("    "):
                        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 4)
                        cursor.removeSelectedText()
                        return  # Event handled

            # 2. Fix Auto-indent on Enter
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

    def set_diff_text(self, diff_text):
        """Sets the content and parses it as a diff to highlight additions/removals."""
        self.diff_lines = {}
        self.custom_line_numbers = {} # block_num -> str(line_num)
        self.clear()
        self.setReadOnly(True)

        lines = diff_text.splitlines()
        clean_lines = []

        import re
        h_pattern = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

        current_old = 1
        current_new = 1
        in_hunk = False

        for line in lines:
            line_idx = len(clean_lines)

            # Ignore standard unified diff file headers
            if line.startswith('+++') or line.startswith('---'):
                continue

            if line.startswith('@@'):
                match = h_pattern.search(line)
                if match:
                    current_old = int(match.group(1))
                    current_new = int(match.group(2))
                    in_hunk = True
                self.diff_lines[line_idx] = '@'
                clean_lines.append(line)
            elif in_hunk:
                if line.startswith('+'):
                    self.diff_lines[line_idx] = '+'
                    self.custom_line_numbers[line_idx] = str(current_new)
                    clean_lines.append(line[1:])
                    current_new += 1
                elif line.startswith('-'):
                    self.diff_lines[line_idx] = '-'
                    self.custom_line_numbers[line_idx] = str(current_old)
                    clean_lines.append(line[1:])
                    current_old += 1
                elif line.startswith(' '):
                    self.custom_line_numbers[line_idx] = str(current_new)
                    clean_lines.append(line[1:])
                    current_old += 1
                    current_new += 1
                elif line == '':
                    # Handle empty lines that diff sometimes produces instead of a space
                    self.custom_line_numbers[line_idx] = str(current_new)
                    clean_lines.append("")
                    current_old += 1
                    current_new += 1
                else:
                    clean_lines.append(line)
            else:
                clean_lines.append(line)

        self.setPlainText('\n'.join(clean_lines))
        self.update_extra_selections()

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
        self.update_extra_selections()

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

        if hasattr(self, 'diff_lines') and self.diff_lines:
            doc = self.document()
            for block_num, marker in self.diff_lines.items():
                if marker in ('+', '-'):
                    selection = QTextEdit.ExtraSelection()
                    # Soft green and red for backgrounds
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
    
        painter.setFont(self.font())
    
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = round(self.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + round(self.blockBoundingRect(block).height())
    
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                # Determine correct line number
                if hasattr(self, 'custom_line_numbers') and block_number in self.custom_line_numbers:
                    number = self.custom_line_numbers[block_number]
                elif hasattr(self, 'diff_lines') and self.diff_lines and block_number in self.diff_lines and self.diff_lines[block_number] == '@':
                    number = "" # Hide number for @@ headers
                elif hasattr(self, 'diff_lines') and self.diff_lines:
                    number = str(block_number + 1) # Fallback for diff context
                else:
                    number = str(block_number + 1)

                if number:
                    painter.setPen(QColor("#858585"))
                    painter.drawText(0, top, self.line_number_area.width() - 40, round(self.blockBoundingRect(block).height()),
                                     Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)

                text_stripped = block.text().strip()
                is_diff_cmd = False
                if text_stripped.startswith("<@|EDIT") or text_stripped.startswith("{!RUN}<@|EDIT"):
                    is_diff_cmd = True
                elif text_stripped.startswith("<@|REFACTOR") or text_stripped.startswith("{!RUN}<@|REFACTOR"):
                    is_diff_cmd = True
                elif (text_stripped.startswith("<@|MANAGE") or text_stripped.startswith("{!RUN}<@|MANAGE")) and "-write" in text_stripped:
                    is_diff_cmd = True

                if is_diff_cmd:
                    diff_rect = QRect(self.line_number_area.width() - 35, top + 2, 32, round(self.blockBoundingRect(block).height()) - 4)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor("#0ea5e9"))
                    painter.drawRoundedRect(diff_rect, 4, 4)
                    painter.setPen(QColor("white"))
                    painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
                    painter.drawText(diff_rect, Qt.AlignmentFlag.AlignCenter, "DIFF")
                    painter.setFont(self.font()) # RESTORE

                # Add DIFF markers (+ / -) next to line number
                if hasattr(self, 'diff_lines') and block_number in self.diff_lines:
                    marker = self.diff_lines[block_number]
                    if marker in ('+', '-'):
                        color = QColor("#a7ffa7") if marker == '+' else QColor("#ff9f9f")
                        painter.setPen(color)
                        painter.setFont(QFont("Consolas", 10, QFont.Bold))
                        marker_rect = QRect(self.line_number_area.width() - 35, top, 15, round(self.blockBoundingRect(block).height()))
                        painter.drawText(marker_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, marker)
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
            is_diff_cmd = False
            if text_stripped.startswith("<@|EDIT") or text_stripped.startswith("{!RUN}<@|EDIT"):
                is_diff_cmd = True
            elif text_stripped.startswith("<@|REFACTOR") or text_stripped.startswith("{!RUN}<@|REFACTOR"):
                is_diff_cmd = True
            elif (text_stripped.startswith("<@|MANAGE") or text_stripped.startswith("{!RUN}<@|MANAGE")) and "-write" in text_stripped:
                is_diff_cmd = True

            if is_diff_cmd:
                self.diff_requested.emit(block.blockNumber())