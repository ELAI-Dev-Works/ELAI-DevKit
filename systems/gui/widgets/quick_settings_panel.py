from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from assets.icons import ICON_QUICK_SETTINGS, svg_to_icon, get_svg_content

class QuickSettingsPanel(QWidget):
    def __init__(self, context_or_window, extension_name_filter: str = None):
        super().__init__()

        # Determine if we got AppContext or MainWindow using QWidget check
        if isinstance(context_or_window, QWidget):
            # It is a Window (MainWindow or LaunchWindow)
            self.main_window = context_or_window
            self.context = getattr(context_or_window, 'context', None)
        else:
            # It is AppContext
            self.context = context_or_window
            self.main_window = getattr(context_or_window, 'main_window', None)

        # Set managers
        if self.context:
            self.lang = self.context.lang
            self.extension_manager = self.context.extension_manager
        elif self.main_window:
            self.lang = self.main_window.lang
            self.extension_manager = self.main_window.extension_manager
        else:
             # Should not happen if correctly initialized
            raise ValueError("QuickSettingsPanel requires a valid Context or MainWindow.")

        self.extension_name_filter = extension_name_filter
        
        self.accordions = {} # To hold {'ext_name': (button, widget)}
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self._populate_quick_settings()
        self.retranslate_ui()

    def _populate_quick_settings(self):
        quick_settings_modules = self.extension_manager.get_extension_quick_settings_modules()
    
        for name, module in quick_settings_modules.items():
            if self.extension_name_filter and name != self.extension_name_filter:
                continue
    
            if not hasattr(module, 'get_quick_settings'):
                continue
    
            try:
                qs_defs = module.get_quick_settings()
            except Exception as e:
                print(f"Error getting quick settings from {name}: {e}")
                continue
    
            for qs_def in qs_defs:
                if qs_def.get('qs_type') != 'panel':
                    continue
    
                widget_class = qs_def['widget_class']
                button = QPushButton()
                button.setCheckable(True)
                button.setStyleSheet("QPushButton { text-align: left; padding: 5px; }")
                
                # Set Icon
                p = self.main_window.theme_manager.current_palette if self.main_window and hasattr(self.main_window, 'theme_manager') else {}
                icon_color = p.get("icon_default", "#e0e0e0")
                button.setIcon(svg_to_icon(get_svg_content(ICON_QUICK_SETTINGS), icon_color))

                content = widget_class(self.context)
    
                button.toggled.connect(content.setVisible)
    
                self.layout.addWidget(button)
                self.layout.addWidget(content)
    
                self.accordions[name] = (button, content)
    
                button.setChecked(False)
                content.setVisible(False)
    
    def retranslate_ui(self):
        for name, (button, content) in self.accordions.items():
            checked = button.isChecked()
            arrow_char = '▼' if checked else '►'
    
            title_key = f'{name}_quick_settings_title'
            title = self.lang.get(title_key)
            button.setText(f"{arrow_char} {title}")
    
            if hasattr(content, 'retranslate_ui'):
                content.retranslate_ui()
    def update_icons(self):
        p = self.main_window.theme_manager.current_palette if self.main_window and hasattr(self.main_window, 'theme_manager') else {}
        icon_color = p.get("icon_default", "#e0e0e0")
        for button, _ in self.accordions.values():
            button.setIcon(svg_to_icon(get_svg_content(ICON_QUICK_SETTINGS), icon_color))