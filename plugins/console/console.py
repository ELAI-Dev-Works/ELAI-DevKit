import sys
import os
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLineEdit, 
    QHBoxLayout, QPushButton, QScrollBar, QStackedWidget,
    QMenu, QFrame
)
import psutil
import subprocess
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QEvent, QPoint
from PySide6.QtGui import QFont, QColor, QPalette, QAction

from systems.os.platform import is_windows, get_shell

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

# --- COLOR PALETTE DEFINITIONS ---
ANSI_COLORS = {
    'black': '#505050',
    'red': '#f14c4c',
    'green': '#23d18b',
    'brown': '#f5f543',
    'blue': '#3b8eea',
    'magenta': '#d670d6',
    'cyan': '#29b8db',
    'white': '#d4d4d4',
    'default': '#d4d4d4',
}

ANSI_COLORS_BRIGHT = {
    'black': '#808080',
    'red': '#f14c4c',
    'green': '#23d18b',
    'brown': '#f5f543',
    'blue': '#3b8eea',
    'magenta': '#d670d6',
    'cyan': '#29b8db',
    'white': '#ffffff',
    'default': '#ffffff'
}

BG_DEFAULT = '#1e1e1e'

class PtyReaderThread(QThread):
    output_received = Signal(str)

    def __init__(self, pty_process):
        super().__init__()
        self.pty = pty_process
        self.running = True

    def run(self):
        while self.running and self.pty.isalive():
            try:
                data = self.pty.read(1024)
                if data:
                    self.output_received.emit(data)
            except Exception:
                break

    def stop(self):
        self.running = False

class ConsoleWidget(QWidget):
    def __init__(self, parent=None, cwd=None, lang=None):
        super().__init__(parent)
        self.cwd = cwd or os.getcwd()
        # Fallback to a mock lang if none provided, to avoid crashes
        if lang:
            self.lang = lang
        else:
            class MockLang:
                def get(self, key): return key
            self.lang = MockLang()
        self.pty = None
        self.reader_thread = None
        self.screen = None
        self.stream = None
        self.history = []
        self.history_idx = 0
        self._last_rendered_html = ""
        
        self._init_ui()
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(30) 
        self.refresh_timer.timeout.connect(self._refresh_display)

        if not (PtyProcess and pyte):
            self.display.setPlainText("Error: 'pywinpty' or 'pyte' libraries are missing.")
            self.start_btn.setEnabled(False)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 1. Display Area
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        self.display.setProperty("no_custom_tooltip", True)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.display.setFont(font)
        self.display.setStyleSheet(f"background-color: {BG_DEFAULT}; color: #cccccc; border: 1px solid #333;")
        self.display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Custom scrollbar
        self.display.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical { background: #1e1e1e; width: 12px; margin: 0; }
            QScrollBar::handle:vertical { background: #444; min-height: 20px; border-radius: 2px; }
            QScrollBar::handle:vertical:hover { background: #555; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        layout.addWidget(self.display)

        # 2. Control Area (Stacked: Start Button vs Input Line)
        self.controls_stack = QStackedWidget()
        self.controls_stack.setFixedHeight(40) # Fixed height for consistency

        # Page 0: Start Button Centered
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

        # Shell Menu Button
        self.shell_btn = QPushButton(self.lang.get('console_shell_btn'))
        self.shell_btn.addGUITooltip(self.lang.get('console_shell_tooltip'))
        self.shell_btn.setFixedWidth(70)
        self.shell_btn.setStyleSheet("background-color: #444; color: #fff; border: 1px solid #555; padding: 4px;")
        self.shell_btn.clicked.connect(self._show_shell_menu)
        input_layout.addWidget(self.shell_btn)

        self.controls_stack.addWidget(self.input_page)
        layout.addWidget(self.controls_stack)

    def _show_shell_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #333; color: #fff; border: 1px solid #555; } QMenu::item:selected { background-color: #555; }")
    
        restart_action = QAction(self.lang.get('console_menu_restart'), self)
        restart_action.triggered.connect(self.restart_session)
        menu.addAction(restart_action)
    
        kill_action = QAction(self.lang.get('console_menu_kill'), self)
        kill_action.triggered.connect(self.stop_session_and_reset)
        menu.addAction(kill_action)

        # Show menu above the button
        pos = self.shell_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(QPoint(pos.x(), pos.y() - menu.sizeHint().height()))

    def start_session(self):
        if self.pty:
            self.stop_session()

        self.cols = 120
        self.rows = 30
        # Increased history limit to 3000 lines as requested
        self.screen = pyte.HistoryScreen(self.cols, self.rows, history=3000)
        self.stream = pyte.Stream(self.screen)

        try:
            shell_cmd = get_shell()
        
            if is_windows():
                self.pty = PtyProcess.spawn(
                    shell_cmd,
                    cwd=self.cwd,
                    dimensions=(self.rows, self.cols)
                )
            else:
                # ptyprocess API differences
                self.pty = PtyProcess.spawn(
                    [shell_cmd],
                    cwd=self.cwd,
                    dimensions=(self.rows, self.cols)
                )
        
            self.reader_thread = PtyReaderThread(self.pty)
            self.reader_thread.output_received.connect(self._on_data_received)
            self.reader_thread.start()
            
            self.refresh_timer.start()
            self.display.clear()
            self.display.append(self.lang.get('console_started_log').format(self.cwd))
            
            # Switch UI to Input mode
            self.controls_stack.setCurrentIndex(1)
            self.input_line.setFocus()
            
        except Exception as e:
            self.display.append(self.lang.get('console_error_pty_log').format(e))
        
    def stop_session(self):
        self.refresh_timer.stop()
        if self.reader_thread:
            self.reader_thread.stop()
    
        if self.pty:
            # Kill process tree to prevent zombie processes (e.g. node, python)
            try:
                pid = self.pty.pid
                if pid:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    try:
                        parent.kill()
                    except psutil.NoSuchProcess:
                        pass
            except (psutil.NoSuchProcess, Exception) as e:
                # Process might be already dead
                pass
    
            try:
                self.pty.close()
            except Exception:
                pass
            self.pty = None
    
        if self.reader_thread:
            if not self.reader_thread.wait(1000):
                self.reader_thread.terminate()
            self.reader_thread = None

    def stop_session_and_reset(self):
        """Stops the shell and returns UI to 'Start' state."""
        self.stop_session()
        self.display.append(f"\n{self.lang.get('console_terminated_log')}")
        self.controls_stack.setCurrentIndex(0)
    
    def restart_session(self):
        self.display.append(f"\n{self.lang.get('console_restarting_log')}")
        self.stop_session()
        self.start_session()

    def send_ctrl_c(self):
        """Sends Ctrl+C (Interrupt) to the PTY."""
        if self.pty:
            # ASCII 3 is ETX (End of Text), widely used as Ctrl+C interrupt
            self.pty.write('\x03') 
            self.display.append("^C")

    def enable_input(self, enabled: bool):
        """Controls whether the input line is editable."""
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

    def _refresh_display(self):
        if not self.screen: return
        vbar = self.display.verticalScrollBar()
        was_at_bottom = vbar.value() >= (vbar.maximum() - 5)
        html_content = self._render_buffer_to_html()
        if len(html_content) != len(self._last_rendered_html) or html_content != self._last_rendered_html:
            self.display.setHtml(html_content)
            self._last_rendered_html = html_content
            if was_at_bottom: vbar.setValue(vbar.maximum())
    
    def _render_line(self, line_data):
        # Safety check: ensure line_data is a dict-like object (pyte Line)
        if not hasattr(line_data, 'get'):
            return ""
    
        current_line_html = []
        current_style = None
        span_text = []
    
        # Iterate over the full width of the screen
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
    
            # Ensure data is a string to prevent vectorcall errors with weird types
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
                    # Construct span style string
                    style_str = f'color:{current_style[0]}; background-color:{current_style[1]};'
                    if current_style[2]: # bold
                        style_str += ' font-weight:bold;'
    
                    current_line_html.append(f'<span style="{style_str}">{ "".join(span_text) }</span>')
                    span_text = []
                current_style = style_key
    
            span_text.append(data)
    
        # Append remaining text
        if current_style is not None:
            style_str = f'color:{current_style[0]}; background-color:{current_style[1]};'
            if current_style[2]:
                style_str += ' font-weight:bold;'
            current_line_html.append(f'<span style="{style_str}">{ "".join(span_text) }</span>')
    
        return "".join(current_line_html)
    

    def _render_buffer_to_html(self):
        lines = []
        lines.append(f'<div style="font-family: Consolas, monospace; font-size: 10pt; background-color: {BG_DEFAULT}; white-space: pre;">')
    
        # 1. Render History (deque)
        for hist_line in self.screen.history:
            lines.append(self._render_line(hist_line) + "<br>")
    
        # 2. Render Active Buffer
        # Trim trailing empty lines so the prompt isn't pushed out of view
        last_active_row = 0
        for row in range(self.screen.lines - 1, -1, -1):
            if any(char.data != ' ' for char in self.screen.buffer[row].values()):
                last_active_row = row
                break

        last_active_row = max(last_active_row, self.screen.cursor.y)

        for row in range(last_active_row + 1):
            line_buffer = self.screen.buffer[row]
            lines.append(self._render_line(line_buffer) + "<br>")
    
        lines.append('</div>')
        return "".join(lines)

    def _get_color_hex(self, color_attr, is_bold=False):
        if color_attr in ANSI_COLORS:
            return ANSI_COLORS_BRIGHT[color_attr] if is_bold and color_attr in ANSI_COLORS_BRIGHT else ANSI_COLORS[color_attr]
        if color_attr == 'default': return ANSI_COLORS_BRIGHT['default'] if is_bold else ANSI_COLORS['default']
        if isinstance(color_attr, str) and color_attr.startswith('#'): return color_attr
        return ANSI_COLORS['default']

    def _send_command(self):
        text = self.input_line.text()
        if not text.strip(): return
        if self.pty:
            self.pty.write(text + "\r\n")
            self.history.append(text)
            self.history_idx = len(self.history)
            self.input_line.clear()

    def send_external_command(self, cmd_string):
        """Auto-starts shell if needed and sends command."""
        if not self.pty:
            self.start_session()
            # Give PTY a moment to initialize if needed, though write buffers usually handle it.
            # In simple terms, pywinpty queue should handle it.
        
        if self.pty:
            self.pty.write(cmd_string + "\r\n")

    def set_cwd(self, path):
        if os.path.isdir(path) and path != self.cwd:
            self.cwd = path
            # Don't auto-start, just update internal state for next time

    def eventFilter(self, obj, event):
        if obj == self.input_line and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                if self.history and self.history_idx > 0:
                    self.history_idx -= 1
                    self.input_line.setText(self.history[self.history_idx])
                elif self.history and self.history_idx == len(self.history):
                     self.history_idx -= 1
                     self.input_line.setText(self.history[self.history_idx])
                return True
            elif key == Qt.Key_Down:
                if self.history and self.history_idx < len(self.history) - 1:
                    self.history_idx += 1
                    self.input_line.setText(self.history[self.history_idx])
                elif self.history_idx == len(self.history) - 1:
                    self.history_idx += 1
                    self.input_line.clear()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        self.stop_session()
        super().closeEvent(event)