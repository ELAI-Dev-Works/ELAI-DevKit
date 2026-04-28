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
from systems.gui.icons import IconManager
from core.gui.main import MainWindow
from systems.documentation.gui.window import DocumentationWindow
from systems.settings.gui.main import SettingsPanel
from systems.extension.gui.extension_manager import ExtensionManagerWidget
from systems.documentation.builder import DocBuilder

class LauncherButton(QFrame):
    clicked = Signal()

    def __init__(self, title, subtitle, icon_ref, callback, parent=None, tooltip=""):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(120)
        if tooltip:
            self.addGUITooltip(tooltip)

        self.callback = callback
        if self.callback:
            self.clicked.connect(self.callback)

        self.icon_ref = icon_ref

        self.normal_color = "#e0e0e0"
        self.hover_color = "#ffffff"
        self.pressed_color = "#aaaaaa"

        # Enable styling
        self.setObjectName("LauncherBtn")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setStyleSheet("border: none; background: transparent;")
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_icon_display()
        layout.addWidget(self.icon_label)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #fff; border: none; background: transparent;")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("font-size: 11pt; color: #aaa; border: none; background: transparent;")
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

    def update_colors(self, normal_color, hover_color="#ffffff", pressed_color="#aaaaaa"):
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self._update_icon_display()

    def _update_icon_display(self, color=None):
        if not color:
            color = self.hover_color if self.underMouse() else self.normal_color
        pixmap = IconManager.get_pixmap(self.icon_ref, color=color, size=64)
        self.icon_label.setPixmap(pixmap)

    def update_texts(self, title, subtitle):
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        return self

    def update_tooltip(self, tooltip):
        self.addGUITooltip(tooltip)
        return self

    def enterEvent(self, event):
        self._update_icon_display(self.hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_icon_display(self.normal_color)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._update_icon_display(self.pressed_color)
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
                self._update_icon_display(self.hover_color)
                self.clicked.emit()
            else:
                self._update_icon_display(self.normal_color)
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

        self.setWindowTitle(self.lang.get('launcher_btn_ext'))
        self.resize(900, 700)

        from systems.gui.utils.windows import center_window
        center_window(self, parent_launcher)

        layout = QVBoxLayout(self)

        # Header with Back button
        header_layout = QHBoxLayout()
        back_btn = QPushButton(self.lang.get('btn_back_to_launcher'))
        p = self.launcher.theme_manager.current_palette
        back_btn.setIcon(IconManager.get_icon("core.home", p.get("icon_default", "#eee")))
        back_btn.clicked.connect(self.close_and_revert)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Manager Widget
        self.manager_widget = ExtensionManagerWidget(self)
        layout.addWidget(self.manager_widget, stretch=1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.reset_btn = QPushButton(self.lang.get('reset_btn'))
        self.apply_btn = QPushButton(self.lang.get('apply_btn'))
        self.save_project_btn = QPushButton(self.lang.get('save_project_btn', 'Save for Current Project'))
        self.save_btn = QPushButton(self.lang.get('save_btn'))

        self.save_project_btn.setEnabled(bool(self.main_window.root_path))

        self.reset_btn.clicked.connect(self.manager_widget.reset_to_defaults)
        self.apply_btn.clicked.connect(lambda: self.apply_settings(is_project=False))
        self.save_project_btn.clicked.connect(lambda: self.save_settings(is_project=True))
        self.save_btn.clicked.connect(lambda: self.save_settings(is_project=False))

        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.save_project_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.store_initial_state()

    def store_initial_state(self):
        saved_settings = self.settings_manager.get_setting(['core'], {})
        if 'extensions' in saved_settings:
            self.state_on_open['extensions'] = saved_settings['extensions'].copy()
        else:
            self.state_on_open['extensions'] = {}

        self.manager_widget.store_initial_state()

    def apply_settings(self, is_project=False):
        self.manager_widget.apply_settings(is_project)

        core_ext = self.state_on_open.get('extensions', {})
        self.settings_manager.update_setting(['core', 'extensions'], core_ext, is_project)

        self.extension_manager.reload_extensions()
        self.manager_widget.retranslate_ui()

        if hasattr(self.main_window, 'reload_tabs'):
            self.main_window.reload_tabs()
        elif hasattr(self.main_window, 'main_window') and self.main_window.main_window:
            if hasattr(self.main_window.main_window, 'reload_tabs'):
                self.main_window.main_window.reload_tabs()

    def save_settings(self, is_project=False):
        self.apply_settings(is_project)
        from PySide6.QtWidgets import QMessageBox
        if is_project:
            self.settings_manager.save_project_settings()
            QMessageBox.information(self, "Success", "Extension settings saved for Current Project.")
        else:
            self.settings_manager.save_settings_file()
            QMessageBox.information(self, "Success", "Global extension settings saved.")

    def close_and_revert(self):
        self.manager_widget.revert_settings()
        self.reject()

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
        self.setMinimumSize(800, 500)

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
        self.logo_label.setFixedSize(96, 96)
        self.logo_label.setStyleSheet("border: none; background: transparent;")
        self.logo_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._set_logo(96)

        title = QLabel("ELAI-DevKit")
        title.setStyleSheet("font-size: 36pt; font-weight: bold;") # Removed hardcoded color
        version_label = QLabel("v135 (core v47)")
        version_label.setStyleSheet("font-size: 13pt; margin-bottom: 5px;") # Removed hardcoded color
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

        self.btn_run = LauncherButton("", "", "core.code", self.launch_main, tooltip=self.lang.get('launcher_run_tooltip'))
        self.btn_docs = LauncherButton("", "", "core.book", self.launch_docs, tooltip=self.lang.get('launcher_docs_tooltip'))
        self.btn_settings = LauncherButton("", "", "core.main_settings", self.launch_settings, tooltip=self.lang.get('launcher_settings_tooltip'))
        self.btn_ext = LauncherButton("", "", "core.extensions", self.launch_extensions, tooltip=self.lang.get('launcher_ext_tooltip'))

        grid.addWidget(self.btn_run, 0, 0)
        grid.addWidget(self.btn_docs, 0, 1)
        grid.addWidget(self.btn_settings, 1, 0)
        grid.addWidget(self.btn_ext, 1, 1)
    
        layout.addLayout(grid)
        layout.addStretch()
    
        self.retranslate_ui()

    def _set_logo(self, size=96):
        pixmap = IconManager.get_pixmap("core.ELAI-DevKit_logo", size=size)
        self.logo_label.setPixmap(pixmap)
    
    def launch_main(self):
        self.hide()
        # Create the window if it doesn't exist yet
        if not hasattr(self, 'main_window') or not self.main_window:
            self.main_window = MainWindow(context=self.context, on_home=self.show_launcher)

        self.main_window.show()
        QApplication.processEvents()
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

        from systems.gui.utils.windows import center_window
        center_window(self.settings_dialog, self)

        layout = QVBoxLayout(self.settings_dialog)
    
        # Header with Back button
        header_layout = QHBoxLayout()
        back_btn = QPushButton(self.lang.get('btn_back_to_launcher'))
        p = self.theme_manager.current_palette
        back_btn.setIcon(IconManager.get_icon("core.home", p.get("icon_default", "#eee")))
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
        icon_active = p.get("icon_active", "#ffffff")
        icon_dim = p.get("icon_dim", "#888888")

        self.setWindowTitle(self.lang.get('window_title'))

        self.btn_run.update_texts(self.lang.get('launcher_btn_run'), self.lang.get('launcher_btn_run_desc')).update_tooltip(self.lang.get('launcher_run_tooltip'))
        self.btn_run.update_colors(icon_def, icon_active, icon_dim)

        self.btn_docs.update_texts(self.lang.get('launcher_btn_docs'), self.lang.get('launcher_btn_docs_desc')).update_tooltip(self.lang.get('launcher_docs_tooltip'))
        self.btn_docs.update_colors(icon_def, icon_active, icon_dim)

        self.btn_settings.update_texts(self.lang.get('launcher_btn_settings'), self.lang.get('launcher_btn_settings_desc')).update_tooltip(self.lang.get('launcher_settings_tooltip'))
        self.btn_settings.update_colors(icon_def, icon_active, icon_dim)

        self.btn_ext.update_texts(self.lang.get('launcher_btn_ext'), self.lang.get('launcher_btn_ext_desc')).update_tooltip(self.lang.get('launcher_ext_tooltip'))
        self.btn_ext.update_colors(icon_def, icon_active, icon_dim)

        # Also update any open dialogs if possible (though mostly modal)
        if hasattr(self, 'settings_dialog') and self.settings_dialog.isVisible():
            self.settings_dialog.setWindowTitle(self.lang.get('launcher_btn_settings'))