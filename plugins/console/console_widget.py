# -*- coding: utf-8 -*-
import sys
import os
import html
import re
import tempfile

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QScrollBar, QStackedWidget, QMenu, QFrame,
    QDialog, QFileDialog, QMessageBox, QApplication, QToolTip
)
import psutil
import subprocess
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QEvent, QPoint, QUrl, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QAction, QDesktopServices, QCursor, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

from systems.os.platform import is_windows, get_shell

from systems.gui.icons import IconManager


# Third-party libraries for Terminal Emulation
try:
    import pyte
    if is_windows():
        from winpty import PtyProcess
    else:
        from ptyprocess import PtyProcess
except ImportError:
    PtyProcess = None
    pyte = None

from .palette import ANSI_COLORS, ANSI_COLORS_BRIGHT, BG_DEFAULT
from .console_display import ConsoleDisplay
from .history_dialog import FullHistoryDialog


class ConsoleWidget(QWidget):
    def __init__(self, parent=None, cwd=None, lang=None):
        super().__init__(parent)
        self.cwd = cwd or os.getcwd()
        if lang:
            self.lang = lang
        else:
            class MockLang:
                def get(self, key): return key
            self.lang = MockLang()
        self.pty = None
        self.reader_thread = None
        self._pty_running = False
        self.screen = None
        self.stream = None
        self.history = []
        self.history_idx = 0

        self._session_log_file = None
        self._session_log_path = None

        self._last_rendered_html = ""
        self._full_history_text = ""

        self._init_ui()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(30)
        self.refresh_timer.timeout.connect(self._refresh_display)

        if not (PtyProcess and pyte):
            self.display.setPlainText("Error: 'pywinpty' or 'pyte' libraries are missing.")
            self.start_btn.setEnabled(False)


    @staticmethod
    def _strip_ansi(text: str) -> str:
        """Remove common ANSI escape sequences from a string."""
        import re
        # CSI sequences (e.g., \x1b[31m, \x1b[?25l, \x1b[6;62H)
        ansi_csi = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]')
        # OSC sequences (e.g., \x1b]0;title\x07)
        ansi_osc = re.compile(r'\x1b\][^\x07]*\x07')
        # Backspace/erase sequences (single \x08)
        ansi_bs = re.compile(r'\x08')
        text = ansi_csi.sub('', text)
        text = ansi_osc.sub('', text)
        text = ansi_bs.sub('', text)
        return text

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 1. Display Area
        display_wrapper = QWidget()
        wrapper_layout = QVBoxLayout(display_wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)

        self.display = ConsoleDisplay()
        self.display.setFont(QFont("Consolas", 10))
        self.display.setStyleSheet(f"background-color: {BG_DEFAULT}; color: #cccccc; border: 1px solid #333;")
        self.display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        self.display.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical { background: #1e1e1e; width: 12px; margin: 0; }
            QScrollBar::handle:vertical { background: #444; min-height: 20px; border-radius: 2px; }
            QScrollBar::handle:vertical:hover { background: #555; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.full_history_btn = QPushButton(self.display)
        self.full_history_btn.setFixedSize(24, 24)
        self.full_history_btn.setCursor(Qt.PointingHandCursor)
        self.full_history_btn.setToolTip("Show Full History")
        self.full_history_btn.setIcon(IconManager.get_icon("core.history", "#cccccc", size=24))
        self.full_history_btn.setIconSize(QSize(24, 24))
        self.full_history_btn.clicked.connect(self._show_full_history)
        self.display.installEventFilter(self)

        wrapper_layout.addWidget(self.display)
        layout.addWidget(display_wrapper)

        # 2. Control Area
        self.controls_stack = QStackedWidget()
        self.controls_stack.setFixedHeight(40)

        # Page 0: Start Button
        self.start_page = QWidget()
        start_layout = QHBoxLayout(self.start_page)
        start_layout.setContentsMargins(0, 0, 0, 0)
        self.start_btn = QPushButton(self.lang.get('console_start_btn'))
        self.start_btn.setFixedWidth(120)
        self.start_btn.setStyleSheet("background-color: #2d5a35; color: white; font-weight: bold; border-radius: 4px; padding: 5px;")
        self.start_btn.clicked.connect(self.start_session)
        start_layout.addStretch()
        start_layout.addWidget(self.start_btn)
        start_layout.addStretch()
        self.controls_stack.addWidget(self.start_page)

        # Page 1: Input Line + Controls
        self.input_page = QWidget()
        input_layout = QHBoxLayout(self.input_page)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)

        self.prompt_label = QLineEdit(">")
        self.prompt_label.setReadOnly(True)
        self.prompt_label.setFixedWidth(40)
        self.prompt_label.setStyleSheet("background: transparent; color: #aaa; border: none; font-weight: bold;")
        self.prompt_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        input_layout.addWidget(self.prompt_label)

        self.input_line = QLineEdit()
        self.input_line.setStyleSheet("background-color: #252526; color: #d4d4d4; border: 1px solid #333; padding: 4px;")
        self.input_line.setPlaceholderText(self.lang.get('console_input_placeholder'))
        self.input_line.returnPressed.connect(self._send_command)
        self.input_line.installEventFilter(self)
        input_layout.addWidget(self.input_line)

        self.clear_btn = QPushButton(self.lang.get('console_clear_btn'))
        self.clear_btn.addGUITooltip(self.lang.get('console_clear_tooltip'))
        self.clear_btn.setFixedWidth(60)
        self.clear_btn.clicked.connect(self.clear_console)
        self.clear_btn.setStyleSheet("background-color: #333; color: #ddd; border: 1px solid #555;")
        input_layout.addWidget(self.clear_btn)

        self.shell_btn = QPushButton(self.lang.get('console_shell_btn'))
        self.shell_btn.addGUITooltip(self.lang.get('console_shell_tooltip'))
        self.shell_btn.setFixedWidth(70)
        self.shell_btn.setStyleSheet("background-color: #444; color: #fff; border: 1px solid #555; padding: 4px;")
        self.shell_btn.clicked.connect(self._show_shell_menu)
        input_layout.addWidget(self.shell_btn)

        self.controls_stack.addWidget(self.input_page)
        layout.addWidget(self.controls_stack)

    def _set_button_icon(self, btn, svg_str, size):
        renderer = QSvgRenderer(svg_str.encode('utf-8'))
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        btn.setIcon(QIcon(pixmap))
        btn.setIconSize(QSize(size, size))

    def eventFilter(self, obj, event):
        if obj == self.display and event.type() == QEvent.Type.Resize:
            self.full_history_btn.move(2, 2)
        if hasattr(self, 'input_line') and obj == self.input_line and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up:
                if self.history and self.history_idx > 0:
                    self.history_idx -= 1
                    self.input_line.setText(self.history[self.history_idx])
                elif self.history and self.history_idx == len(self.history):
                    self.history_idx -= 1
                    self.input_line.setText(self.history[self.history_idx])
                return True
            elif key == Qt.Key.Key_Down:
                if self.history and self.history_idx < len(self.history) - 1:
                    self.history_idx += 1
                    self.input_line.setText(self.history[self.history_idx])
                elif self.history_idx == len(self.history) - 1:
                    self.history_idx += 1
                    self.input_line.clear()
                return True
        return super().eventFilter(obj, event)

    def _show_shell_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #333; color: #fff; border: 1px solid #555; } QMenu::item:selected { background-color: #555; }")
        restart_action = QAction(self.lang.get('console_menu_restart'), self)
        restart_action.triggered.connect(self.restart_session)
        menu.addAction(restart_action)
        kill_action = QAction(self.lang.get('console_menu_kill'), self)
        kill_action.triggered.connect(self.stop_session_and_reset)
        menu.addAction(kill_action)
        pos = self.shell_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(QPoint(pos.x(), pos.y() - menu.sizeHint().height()))

    def _show_full_history(self):
        if self._session_log_path and os.path.exists(self._session_log_path):
            try:
                with open(self._session_log_path, 'rb') as f:
                    raw = f.read()
                self._full_history_text = raw.decode('utf-8', errors='replace')
            except Exception:
                self._collect_full_history()
        else:
            self._collect_full_history()
        dialog = FullHistoryDialog(self._full_history_text, self)
        dialog.exec()

    def _collect_full_history(self):
        lines = []
        if self.screen:
            for hist_line in self.screen.history:
                lines.append(self._line_to_plain_text(hist_line))
            last_active_row = 0
            for row in range(self.screen.lines - 1, -1, -1):
                if any(char.data != ' ' for char in self.screen.buffer[row].values()):
                    last_active_row = row
                    break
            last_active_row = max(last_active_row, self.screen.cursor.y)
            for row in range(last_active_row + 1):
                lines.append(self._line_to_plain_text(self.screen.buffer[row]))
        self._full_history_text = "\n".join(lines)

    def _line_to_plain_text(self, line_data):
        if not hasattr(line_data, 'get'):
            return ""
        chars = []
        for col in range(self.screen.columns):
            char = line_data.get(col)
            if char:
                chars.append(char.data)
            else:
                chars.append(" ")
        return "".join(chars).rstrip()

    def start_session(self):
        if self.pty:
            self.stop_session()
        self.cols = 120
        self.rows = 30
        self.screen = pyte.HistoryScreen(self.cols, self.rows, history=3000)
        self.stream = pyte.Stream(self.screen)
        self._full_history_text = ""

        try:
            shell_cmd = get_shell()
            if is_windows():
                self.pty = PtyProcess.spawn(shell_cmd, cwd=self.cwd, dimensions=(self.rows, self.cols))
            else:
                self.pty = PtyProcess.spawn([shell_cmd], cwd=self.cwd, dimensions=(self.rows, self.cols))

            if self.pty and self.pty.pid:
                from systems.async_thread.process_utils import ProcessManager
                ProcessManager.register_process(self.pty.pid)

            self._pty_running = True

            # --- Session log file ---
            if self._session_log_path and os.path.exists(self._session_log_path):
                os.remove(self._session_log_path)
            log_fd, self._session_log_path = tempfile.mkstemp(suffix='.log', prefix='elai_console_')
            os.close(log_fd)
            self._session_log_file = open(self._session_log_path, 'ab')
            self._session_log_file.write(b"=== Console session started ===\n")


            # Find thread control via manager
            mw = self.window()
            tc = None
            if hasattr(mw, 'async_thread_manager'):
                tc = mw.async_thread_manager.thread
            elif hasattr(mw, 'main_window') and hasattr(mw.main_window, 'async_thread_manager'):
                tc = mw.main_window.async_thread_manager.thread

            if not tc:
                from systems.async_thread.thread_control import ThreadControl
                self._fallback_tc = ThreadControl()
                tc = self._fallback_tc

            self.reader_thread = tc.run_dedicated_thread(
                self._pty_reader_task,
                yield_callback=self._on_data_received,
                use_qt=True,
                thread_name="PtyReader"
            )

            self.refresh_timer.start()
            self.display.clear()
            self.display.append(self.lang.get('console_started_log').format(self.cwd))
            self.controls_stack.setCurrentIndex(1)
            self.input_line.setFocus()
        except Exception as e:
            self.display.append(self.lang.get('console_error_pty_log').format(e))


    def _pty_reader_task(self):
        while self._pty_running and self.pty and self.pty.isalive():
            try:
                data = self.pty.read(1024)
                if data:
                    yield data
            except Exception:
                break

    def stop_session(self):
        self.refresh_timer.stop()

        if self._session_log_file:
            self._session_log_file.close()
            self._session_log_file = None

        self._pty_running = False
        if self.reader_thread:
            self.reader_thread.requestInterruption()
        if self.pty:
            try:
                pid = self.pty.pid
                if pid:
                    from systems.async_thread.process_utils import ProcessManager
                    ProcessManager.kill_process_tree(pid)
            except Exception:
                pid = None
                pass
            try:
                self.pty.close()
            except Exception:
                pass

            if pid:
                from systems.async_thread.process_utils import ProcessManager
                ProcessManager.unregister_process(pid)

            self.pty = None
        if self.reader_thread:
            if not self.reader_thread.wait(1000):
                self.reader_thread.terminate()
            self.reader_thread = None

    def stop_session_and_reset(self):
        self.stop_session()
        self.display.append(f"\n{self.lang.get('console_terminated_log')}")
        self.controls_stack.setCurrentIndex(0)

    def restart_session(self):
        self.display.append(f"\n{self.lang.get('console_restarting_log')}")
        self.stop_session()
        self.start_session()

    def send_ctrl_c(self):
        if self.pty:
            self.pty.write('\x03')
            self.display.append("^C")

    def enable_input(self, enabled: bool):
        self.input_line.setEnabled(enabled)
        if not enabled:
            self.input_line.setPlaceholderText(self.lang.get('console_input_disabled_placeholder'))
        else:
            self.input_line.setPlaceholderText(self.lang.get('console_input_placeholder'))

    def is_running(self):
        return self.pty is not None

    def clear_console(self):
        if self.screen:
            self.screen.reset()
        self.display.clear()

    def _on_data_received(self, data):
        if self.stream:
            self.stream.feed(data)

            # Layer 1: Detect localhost ports and register them
            if isinstance(data, bytes):
                text_data = data.decode('utf-8', errors='ignore')
            else:
                text_data = data

            import re
            # Match localhost:port or 127.0.0.1:port
            match = re.search(r'(?:localhost|127\.0\.0\.1):(\d+)', text_data)
            if match:
                port = int(match.group(1))
                mw = self.window()
                if hasattr(mw, 'context') and hasattr(mw.context, 'security_manager'):
                    mw.context.security_manager.register_local_server(port)

            if self._session_log_file:
                # Convert data to bytes for writing
                raw_bytes = data if isinstance(data, bytes) else data.encode('utf-8', errors='replace')
                # Decode to string, strip ANSI, re‑encode for log cleanliness
                text = raw_bytes.decode('utf-8', errors='replace')
                clean_text = self._strip_ansi(text)
                self._session_log_file.write(clean_text.encode('utf-8', errors='replace'))
                self._session_log_file.flush()

    def _refresh_display(self):
        if not self.screen:
            return
        vbar = self.display.verticalScrollBar()
        was_at_bottom = vbar.value() >= (vbar.maximum() - 5)
        html_content = self._render_buffer_to_html()
        if len(html_content) != len(self._last_rendered_html) or html_content != self._last_rendered_html:
            self.display.setHtml(html_content)
            self._last_rendered_html = html_content
            if was_at_bottom:
                vbar.setValue(vbar.maximum())

    def _render_buffer_to_html(self):
        lines = []
        lines.append(f'<div style="font-family: Consolas, monospace; font-size: 10pt; background-color: {BG_DEFAULT}; white-space: pre;">')
        if self.screen:
            for hist_line in self.screen.history:
                lines.append(self._render_line(hist_line) + "<br>")
            last_active_row = 0
            for row in range(self.screen.lines - 1, -1, -1):
                if any(char.data != ' ' for char in self.screen.buffer[row].values()):
                    last_active_row = row
                    break
            last_active_row = max(last_active_row, self.screen.cursor.y)
            for row in range(last_active_row + 1):
                lines.append(self._render_line(self.screen.buffer[row]) + "<br>")
        lines.append('</div>')
        html_str = "".join(lines)
        html_str = self._linkify_urls(html_str)
        return html_str

    def _linkify_urls(self, html_text):
        url_pattern = re.compile(r'(?<![="])\b(https?://[^\s<>"]+?)(?=[\s<"&]|$)')
        def replacer(match):
            url = match.group(0)
            return f'<a href="{url}" style="color: #3b8eea; text-decoration: underline;" title="Ctrl+Click or double-click to open in browser">{url}</a>'
        return url_pattern.sub(replacer, html_text)

    def _render_line(self, line_data):
        if not hasattr(line_data, 'get'):
            return ""
        current_line_html = []
        current_style = None
        span_text = []
        cols = self.screen.columns
        for col in range(cols):
            char = line_data.get(col)
            if char:
                data = char.data
                fg = char.fg
                bg = char.bg
                bold = char.bold
            else:
                data = " "
                fg = "default"
                bg = "default"
                bold = False

            data = str(data)
            data = html.escape(data)
            fg_color = self._get_color_hex(fg, bold)
            if bg == 'default':
                bg_color = 'transparent'
            elif bg in ANSI_COLORS:
                bg_color = ANSI_COLORS[bg]
            elif isinstance(bg, str) and bg.startswith('#'):
                bg_color = bg
            else:
                bg_color = 'transparent'

            style_key = (fg_color, bg_color, bold)
            if style_key != current_style:
                if current_style is not None:
                    style_str = f'color:{current_style[0]}; background-color:{current_style[1]};'
                    if current_style[2]:
                        style_str += ' font-weight:bold;'
                    current_line_html.append(f'<span style="{style_str}">{ "".join(span_text) }</span>')
                    span_text = []
                current_style = style_key
            span_text.append(data)

        if current_style is not None:
            style_str = f'color:{current_style[0]}; background-color:{current_style[1]};'
            if current_style[2]:
                style_str += ' font-weight:bold;'
            current_line_html.append(f'<span style="{style_str}">{ "".join(span_text) }</span>')
        return "".join(current_line_html)

    def _get_color_hex(self, color_attr, is_bold=False):
        if color_attr in ANSI_COLORS:
            return ANSI_COLORS_BRIGHT[color_attr] if is_bold and color_attr in ANSI_COLORS_BRIGHT else ANSI_COLORS[color_attr]
        if color_attr == 'default':
            return ANSI_COLORS_BRIGHT['default'] if is_bold else ANSI_COLORS['default']
        if isinstance(color_attr, str) and color_attr.startswith('#'):
            return color_attr
        return ANSI_COLORS['default']

    def _send_command(self):
        text = self.input_line.text()
        if not text.strip():
            return
        if self.pty:
            self.pty.write(text + "\r\n")
            self.history.append(text)
            self.history_idx = len(self.history)
            self.input_line.clear()

    def send_external_command(self, cmd_string):
        if not self.pty:
            self.start_session()
        if self.pty:
            self.pty.write(cmd_string + "\r\n")

    def set_cwd(self, path):
        if os.path.isdir(path) and path != self.cwd:
            self.cwd = path

    def closeEvent(self, event):
        self.stop_session()
        super().closeEvent(event)