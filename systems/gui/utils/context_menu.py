from PySide6.QtWidgets import QTextEdit, QPlainTextEdit
from PySide6.QtGui import QKeySequence
from PySide6.QtCore import Qt

class ContextMenuManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def setup(self):
        """
        Initializes the context menu system.
        Extensions register widgets via register_widget().
        """
        self.registry = {} # widget -> [list of provider callbacks]
    
        # Register default widgets (like the main log output)
        self.register_widget(self.main_window.patcher_log_output)
    
    def register_widget(self, widget, provider_callback=None):
        """
        Registers a widget for custom context menus.
        :param widget: The Qt widget instance.
        :param provider_callback: A function(menu, widget) that adds actions to the menu.
        """
        if widget not in self.registry:
            self.registry[widget] = []
            widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            widget.customContextMenuRequested.connect(
                lambda pos, w=widget: self.show_context_menu(pos, w)
            )
    
        if provider_callback:
            self.registry[widget].append(provider_callback)
    
    def show_context_menu(self, pos, source_widget):
        """Creates and shows the context menu, invoking registered providers."""
        if not isinstance(source_widget, (QTextEdit, QPlainTextEdit)):
            return
    
        menu = source_widget.createStandardContextMenu()
    
        # Add global actions (e.g. Select All)
        menu.addSeparator()
        select_all_action = menu.addAction(self.main_window.lang.get('select_all_action'))
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(source_widget.selectAll)
    
        # Call registered providers to extend the menu
        if source_widget in self.registry:
            for provider in self.registry[source_widget]:
                try:
                    provider(menu, source_widget)
                except Exception as e:
                    print(f"Error in context menu provider: {e}")
    
        menu.exec(source_widget.mapToGlobal(pos))