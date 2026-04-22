from PySide6.QtWidgets import QApplication, QTextEdit, QPlainTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QAction

class KeyManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def setup_shortcuts(self):
        """Creates and connects global shortcuts for text editing."""
        
        def get_focused_widget():
            widget = QApplication.focusWidget()
            if isinstance(widget, (QTextEdit, QPlainTextEdit)):
                return widget
            return None

        copy_action = QAction(self.main_window)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(lambda: get_focused_widget().copy() if get_focused_widget() else None)
        
        paste_action = QAction(self.main_window)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(lambda: get_focused_widget().paste() if get_focused_widget() else None)

        cut_action = QAction(self.main_window)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(lambda: get_focused_widget().cut() if get_focused_widget() else None)

        select_all_action = QAction(self.main_window)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(lambda: get_focused_widget().selectAll() if get_focused_widget() else None)
        
        undo_action = QAction(self.main_window)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(lambda: get_focused_widget().undo() if get_focused_widget() else None)
        
        redo_action = QAction(self.main_window)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(lambda: get_focused_widget().redo() if get_focused_widget() else None)

        self.main_window.addActions([
            copy_action, paste_action, cut_action,
            select_all_action, undo_action, redo_action
        ])
    
    def register_shortcut(self, sequence_str, callback, context_widget=None):
        """
        Registers a custom shortcut.
        :param sequence_str: Key sequence string (e.g., "Ctrl+Shift+P").
        :param callback: Function to call when triggered.
        :param context_widget: If provided, shortcut works only when this widget has focus/context.
                                If None, it is application-global (attached to MainWindow).
        """
        target = context_widget if context_widget else self.main_window
        action = QAction(target)
        action.setShortcut(QKeySequence(sequence_str))
        action.triggered.connect(callback)
        if context_widget:
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        target.addAction(action)
        