from PySide6.QtWidgets import (
QApplication,
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QGridLayout, QDialog, QScrollArea
    , QMessageBox
)
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from systems.extension.app_context import AppContext
from assets.icons import ICON_CODE, ICON_BOOK, ICON_MAIN_SETTINGS, ICON_EXTENSIONS, ICON_HOME, ICON_LOGO, svg_to_icon, get_svg_content
from core.gui.main import MainWindow
from systems.documentation.gui.window import DocumentationWindow
from systems.settings.gui.main import SettingsPanel
from systems.extension.gui.extension_manager import ExtensionManagerWidget
from systems.documentation.builder import DocBuilder

class LauncherButton(QFrame):
    clicked = Signal()

    def __init__(self, title, subtitle, svg_icon, callback, parent=None, tooltip=""):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(100)
        if tooltip:
            self.addGUITooltip(tooltip)

        self.callback = callback
        if self.callback:
            self.clicked.connect(self.callback)

        self.svg_icon_data = svg_icon

        # Enable styling
        self.setObjectName("LauncherBtn")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)
        self.icon_label.setStyleSheet("border: none; background: transparent;")
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_icon_color("#e0e0e0")
        layout.addWidget(self.icon_label)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #fff; border: none; background: transparent;")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("font-size: 10pt; color: #aaa; border: none; background: transparent;")
        self.subtitle_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)
        text_layout.addStretch()

        layout.addLayout(text_layout)
        layout.addStretch()

        self.setStyleSheet("""
            #LauncherBtn {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 8px;
            }
            #LauncherBtn:hover {
                background-color: #333;
                border: 1px solid #666;
            }
        """)

    def _set_icon_color(self, color):
        # 1. Prepare SVG data with the correct color
        data = self.svg_icon_data.replace("currentColor", color).encode('utf-8')
    
        # 2. Create a renderer
        renderer = QSvgRenderer(data)
    
        # 3. Create a high-quality pixmap of the target size
        # Using 48x48 to match the label size directly (crisp rendering)
        size = 48
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
    
        # 4. Paint the SVG onto the pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
    
        self.icon_label.setPixmap(pixmap)

    def update_texts(self, title, subtitle):
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        return self
    def update_tooltip(self, tooltip):
        self.addGUITooltip(tooltip)
        return self

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
             self.setStyleSheet("""
            #LauncherBtn {
                background-color: #222;
                border: 1px solid #555;
                border-radius: 8px;
            }
            """)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Restore hover style
            self.setStyleSheet("""
            #LauncherBtn {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 8px;
            }
            #LauncherBtn:hover {
                background-color: #333;
                border: 1px solid #666;
            }
            """)
            if self.rect().contains(event.pos()):
                self.clicked.emit()
        super().mouseReleaseEvent(event)


class ExtensionsWindow(QDialog):
    """Standalone window for extensions management and settings."""
    def __init__(self, parent_launcher):
        super().__init__(parent_launcher)
        self.launcher = parent_launcher
        self.main_window = parent_launcher # Proxy for widgets that expect main_window
        self.lang = parent_launcher.lang
        self.settings_manager = parent_launcher.context.settings_manager
        self.extension_manager = parent_launcher.context.extension_manager

        self.state_on_open = {}
        self.extension_settings_widgets = {}

        self.setWindowTitle(self.lang.get('launcher_btn_ext'))
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        # Header with Back button
        header_layout = QHBoxLayout()
        back_btn = QPushButton(self.lang.get('btn_back_to_launcher'))
        p = self.launcher.theme_manager.current_palette
        back_btn.setIcon(svg_to_icon(get_svg_content(ICON_HOME), p.get("icon_default", "#eee")))
        back_btn.clicked.connect(self.close_and_revert)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Manager Widget
        self.manager_widget = ExtensionManagerWidget(self)
        self.extension_settings_widgets['extensions_manager'] = self.manager_widget
        layout.addWidget(self.manager_widget)

        # Settings Accordions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        settings_container = QWidget()
        self.settings_layout = QVBoxLayout(settings_container)
        scroll.setWidget(settings_container)
        layout.addWidget(scroll, stretch=1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.reset_btn = QPushButton(self.lang.get('reset_btn'))
        self.apply_btn = QPushButton(self.lang.get('apply_btn'))
        self.save_btn = QPushButton(self.lang.get('save_btn'))

        self.reset_btn.clicked.connect(self.reset_to_defaults)
        self.apply_btn.clicked.connect(self.apply_settings)
        self.save_btn.clicked.connect(self.save_settings)

        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.store_initial_state()
        self._populate_settings()

    def _populate_settings(self):
        while self.settings_layout.count() > 0:
            item = self.settings_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        keys_to_remove = [k for k in self.extension_settings_widgets if k != 'extensions_manager']
        for k in keys_to_remove: del self.extension_settings_widgets[k]

        ext_settings_classes = self.extension_manager.get_extension_settings_widgets()
        for name, settings_class in ext_settings_classes.items():
            if self.extension_manager.extensions[name].get('enabled'):
                widget = settings_class(self.main_window)
                self.extension_settings_widgets[name] = widget
                if hasattr(widget, 'store_initial_state'):
                    widget.store_initial_state()

                title = self.extension_manager.extensions[name].get('display_name', name)
                btn = QPushButton(f"► {title} Settings")
                btn.setCheckable(True)
                btn.setStyleSheet("text-align: left; padding: 5px; font-weight: bold; border: 1px solid transparent;")

                widget.setVisible(False)

                def make_toggle(w, b, t):
                    return lambda checked: (w.setVisible(checked), b.setText(f"{'▼' if checked else '►'} {t} Settings"))

                btn.toggled.connect(make_toggle(widget, btn, title))

                self.settings_layout.addWidget(btn)
                self.settings_layout.addWidget(widget)
        self.settings_layout.addStretch()

    def store_initial_state(self):
        saved_settings = self.settings_manager.get_setting(['core'], {})
        if 'extensions' in saved_settings:
            self.state_on_open['extensions'] = saved_settings['extensions'].copy()
        else:
            self.state_on_open['extensions'] = {}

        for widget in self.extension_settings_widgets.values():
            if hasattr(widget, 'store_initial_state'):
                widget.store_initial_state()

    def apply_settings(self):
        for widget in self.extension_settings_widgets.values():
            if hasattr(widget, 'apply_settings'):
                widget.apply_settings()

        core_settings = self.settings_manager.load_settings_file().get('core', {})
        if 'extensions' not in core_settings:
            core_settings['extensions'] = {}
        core_settings['extensions'].update(self.state_on_open.get('extensions', {}))
        self.settings_manager.update_setting(['core'], core_settings)

        self.extension_manager.reload_extensions()
        self._populate_settings()

    def save_settings(self):
        self.apply_settings()
        core_settings = self.settings_manager.load_settings_file().get('core', {})
        if 'extensions' not in core_settings:
            core_settings['extensions'] = {}
        core_settings['extensions'].update(self.state_on_open.get('extensions', {}))
        self.settings_manager.update_setting(['core'], core_settings)

        for name, widget in self.extension_settings_widgets.items():
            if name == 'extensions_manager': continue
            if hasattr(widget, 'get_settings_to_save'):
                ind_settings = widget.get_settings_to_save()
                if ind_settings:
                    self.settings_manager.update_setting(['apps', name, 'settings'], ind_settings)

        self.settings_manager.save_settings_file()
        QMessageBox.information(self, "Success", "Extension settings saved.")

    def close_and_revert(self):
        for widget in self.extension_settings_widgets.values():
            if hasattr(widget, 'revert_settings'):
                widget.revert_settings()
        self.reject()

    def reset_to_defaults(self):
        for widget in self.extension_settings_widgets.values():
            if hasattr(widget, 'reset_to_defaults'):
                widget.reset_to_defaults()

class LaunchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_root_path = self._get_app_root()
        
        # Init Context
        self.context = AppContext(self.app_root_path, self)
        self.root_path = None # Required by some managers
        
        # Shortcut accessors for child widgets
        self.lang = self.context.lang
        self.settings_manager = self.context.settings_manager
        self.theme_manager = self.context.theme_manager
        self.extension_manager = self.context.extension_manager
        
        self.setWindowTitle("ELAI-DevKit Launcher")
        self.setFixedSize(800, 500)
        
        # Apply theme initially
        self._apply_initial_theme()
        
        self._init_ui()
    
        # Build documentation on startup
        try:
            builder = DocBuilder(self.app_root_path)
            builder.build()
        except Exception as e:
            print(f"Error building documentation: {e}")
    
    def _get_app_root(self):
        import os
        # Go up two levels from gui/windows/ to get to the project root
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    def _apply_initial_theme(self):
        core_settings = self.context.settings_manager.get_setting(['core'], {})
        theme_settings = core_settings.get('theme', {})

        # New format only: color_scheme + theme
        color_scheme = theme_settings.get('color_scheme', 'dark')
        theme = theme_settings.get('theme', 'sleek')

        # Validate color_scheme
        available_colors = self.theme_manager.get_available_color_schemes()
        if color_scheme not in available_colors:
            color_scheme = 'dark'
        
        # Validate theme
        available_themes = self.theme_manager.get_available_themes()
        if theme not in available_themes:
            theme = 'sleek'

        self.theme_manager.apply_theme(color_scheme, theme)
    
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
    
        # Header
        header_layout = QHBoxLayout()

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(64, 64)
        self.logo_label.setStyleSheet("border: none; background: transparent;")
        self.logo_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._set_logo(64)

        title = QLabel("ELAI-DevKit")
        title.setStyleSheet("font-size: 32pt; font-weight: bold;") # Removed hardcoded color
        version_label = QLabel("v129 (core v44)")
        version_label.setStyleSheet("font-size: 12pt; margin-bottom: 5px;") # Removed hardcoded color
        version_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
    
        header_layout.addWidget(self.logo_label)
        header_layout.addWidget(title)
        header_layout.addWidget(version_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
    
        layout.addSpacing(30)
    
        # Grid for buttons
        grid = QGridLayout()
        grid.setSpacing(20)
    
        self.btn_run = LauncherButton("", "", get_svg_content(ICON_CODE), self.launch_main, tooltip=self.lang.get('launcher_run_tooltip'))
        self.btn_docs = LauncherButton("", "", get_svg_content(ICON_BOOK), self.launch_docs, tooltip=self.lang.get('launcher_docs_tooltip'))
        self.btn_settings = LauncherButton("", "", get_svg_content(ICON_MAIN_SETTINGS), self.launch_settings, tooltip=self.lang.get('launcher_settings_tooltip'))
        self.btn_ext = LauncherButton("", "", get_svg_content(ICON_EXTENSIONS), self.launch_extensions, tooltip=self.lang.get('launcher_ext_tooltip'))
    
        grid.addWidget(self.btn_run, 0, 0)
        grid.addWidget(self.btn_docs, 0, 1)
        grid.addWidget(self.btn_settings, 1, 0)
        grid.addWidget(self.btn_ext, 1, 1)
    
        layout.addLayout(grid)
        layout.addStretch()
    
        self.retranslate_ui()

    def _set_logo(self, size=64):
        svg_data = get_svg_content(ICON_LOGO)
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        self.logo_label.setPixmap(pixmap)
    
    def launch_main(self):
        self.hide()
        self.main_window = MainWindow(context=self.context, on_home=self.show_launcher)
        self.main_window.show()
        # Don't close, just hide, so we can show it again
    
    def launch_docs(self):
        self.hide()
        self.doc_window = DocumentationWindow(self.context, on_home=self.show_launcher)
        self.doc_window.show()
    
    def show_launcher(self):
        self.show()
    
    def launch_settings(self):
        # We wrap SettingsPanel in a Dialog
        self.settings_dialog = QDialog(self)
        self.settings_dialog.setWindowTitle(self.lang.get('launcher_btn_settings'))
        self.settings_dialog.resize(700, 600)
        layout = QVBoxLayout(self.settings_dialog)
    
        # Header with Back button
        header_layout = QHBoxLayout()
        back_btn = QPushButton(self.lang.get('btn_back_to_launcher'))
        p = self.theme_manager.current_palette
        back_btn.setIcon(svg_to_icon(get_svg_content(ICON_HOME), p.get("icon_default", "#eee")))
        back_btn.clicked.connect(self.settings_dialog.close)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)
    
        # SettingsPanel expects a MainWindow as parent to access attributes.
        # Self (LaunchWindow) acts as that proxy.
        panel = SettingsPanel(self)
        panel.store_initial_state()
        panel.retranslate_ui()
        panel.closed.connect(self.settings_dialog.reject)
        # Hide the 'Extensions Settings' tab in this view as requested
        panel.tab_widget.setTabVisible(2, False)

        layout.addWidget(panel)
        self.settings_dialog.exec()
    
    def launch_extensions(self):
        dialog = ExtensionsWindow(self)
        dialog.exec()
    
    # --- Proxy methods for SettingsPanel compatibility ---
    def apply_main_settings(self, settings):
        """Applies the main settings centrally to the entire application."""
        if 'language' in settings:
            self.lang.set_language(settings['language'])

        if 'ui' in settings:
            app = QApplication.instance()
            if hasattr(app, '_tooltip_enhancer'):
                app._tooltip_enhancer.always_show = settings['ui'].get('always_show_tooltips', False)

        # Theme settings are now handled directly by the ThemeManager
        # based on its current state, which is updated via the settings panel.
        # This method is now primarily for language updates.

        # Update text immediately
        self.retranslate_ui()
    
    def retranslate_ui(self):
        p = self.theme_manager.current_palette
        icon_def = p.get("icon_default", "#e0e0e0")

        self.setWindowTitle(self.lang.get('window_title'))

        self.btn_run.update_texts(self.lang.get('launcher_btn_run'), self.lang.get('launcher_btn_run_desc')).update_tooltip(self.lang.get('launcher_run_tooltip'))
        self.btn_run._set_icon_color(icon_def)

        self.btn_docs.update_texts(self.lang.get('launcher_btn_docs'), self.lang.get('launcher_btn_docs_desc')).update_tooltip(self.lang.get('launcher_docs_tooltip'))
        self.btn_docs._set_icon_color(icon_def)

        self.btn_settings.update_texts(self.lang.get('launcher_btn_settings'), self.lang.get('launcher_btn_settings_desc')).update_tooltip(self.lang.get('launcher_settings_tooltip'))
        self.btn_settings._set_icon_color(icon_def)

        self.btn_ext.update_texts(self.lang.get('launcher_btn_ext'), self.lang.get('launcher_btn_ext_desc')).update_tooltip(self.lang.get('launcher_ext_tooltip'))
        self.btn_ext._set_icon_color(icon_def)
    
        # Also update any open dialogs if possible (though mostly modal)
        if hasattr(self, 'settings_dialog') and self.settings_dialog.isVisible():
            self.settings_dialog.setWindowTitle(self.lang.get('launcher_btn_settings'))
        pass