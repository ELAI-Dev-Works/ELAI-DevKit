from PySide6.QtWidgets import QDialog, QVBoxLayout
from plugins.code_editor.editor_textarea import CodeEditor

class MaximizedEditorDialog(QDialog):
    def __init__(self, source_editor, parent=None):
        super().__init__(parent)
        self.source_editor = source_editor
        self.setWindowTitle("Code Editor (Maximized)")
        self.resize(1000, 700)

        if hasattr(source_editor, '_last_palette'):
            bg = source_editor._last_palette.get("background", "#1e1e1e")
            self.setStyleSheet(f"QDialog {{ background-color: {bg}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.max_editor = CodeEditor(self)
        self.max_editor.settings_panel.maximize_btn.hide()

        # Link document and copy relevant settings
        self.max_editor.setDocument(source_editor.document())
        self.max_editor.diff_lines = getattr(source_editor, 'diff_lines', {})
        self.max_editor.custom_line_numbers = getattr(source_editor, 'custom_line_numbers', {})
        self.max_editor.command_order_map = getattr(source_editor, 'command_order_map', {})
        self.max_editor.setReadOnly(source_editor.isReadOnly())

        # Replicate right panel state
        if hasattr(source_editor, '_right_panel_enabled'):
            self.max_editor.set_right_panel_enabled(source_editor._right_panel_enabled)

        if hasattr(source_editor, '_last_palette'):
            self.max_editor.update_theme_colors(source_editor._last_palette)

        # Connect diff requested signal
        if hasattr(source_editor, 'diff_requested'):
            self.max_editor.diff_requested.connect(source_editor.diff_requested.emit)

        layout.addWidget(self.max_editor)
        self.finished.connect(self._sync_cursor)

    def _sync_cursor(self):
        self.source_editor.setTextCursor(self.max_editor.textCursor())