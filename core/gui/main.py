from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QApplication, QFileDialog, QLabel,
        QMessageBox,
        QFrame, QStackedLayout, QTabWidget, QTabBar
    )
from PySide6.QtCore import Qt
import os

from systems.settings.manager import SettingsManager
from systems.language.manager import LanguageManager
from systems.extension.manager import ExtensionManager
from systems.extension.args import ArgsManager
from systems.gui.widgets.log_box import LogBox
from systems.project.ignore_handler import IgnoreHandler
from systems.gui.utils.context_menu import ContextMenuManager
from systems.gui.utils.key_manager import KeyManager
from systems.gui.themes.manager import ThemeManager
from systems.settings.gui.main import SettingsPanel
from systems.gui.widgets.quick_settings_panel import QuickSettingsPanel
from assets.icons import ICON_HOME, ICON_MAIN_SETTINGS, ICON_DETACH, svg_to_icon, get_svg_content

# Special code that will signal launch.py that a restart is needed
RESTART_CODE = 100

class DetachedTabWindow(QMainWindow):
    def __init__(self, main_window, widget, name, title):
        super().__init__()
        self.main_window = main_window
        self.widget = widget
        self.name = name
        self.setWindowTitle(title)
        self.setCentralWidget(widget)
        self.widget.show()
        self.resize(900, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    def closeEvent(self, event):
        if hasattr(self.main_window, 'detached_tabs') and self.name in self.main_window.detached_tabs:
            self.main_window.attach_tab(self.name)
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self, run_gui=True, context=None, on_home=None):
        super().__init__()
    
        self.root_path = None
        if context:
            context.main_window = self
        self.context = context
        self.app_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.tabs = {}
        self.on_home_callback = on_home
    
        if context:
            # Reuse managers from the context
            self.settings_manager = context.settings_manager
            self.lang = context.lang
            self.theme_manager = context.theme_manager
            # Update the window reference in theme manager so it can find path_label
            self.theme_manager.main_window = self
    
            self.extension_manager = context.extension_manager
            # Update main_window reference in extension manager
            self.extension_manager.main_window = self
            # Also update references in all initialized extension app instances
            for meta in self.extension_manager.extensions.values():
                if meta.get("instance") and hasattr(meta["instance"], "main_window"):
                    meta["instance"].main_window = self
        else:
            # Fallback initialization (legacy or standalone test)
            self.settings_manager = SettingsManager(self.app_root_path)
            self.lang = LanguageManager(self.app_root_path)
            self.theme_manager = ThemeManager(self)
    
            main_settings = self.settings_manager.load_settings('main')
            self.lang.set_language(main_settings.get('Language', {}).get('language', 'en'))
    
            self.extension_manager = ExtensionManager(self)
            self.extension_manager.discover_extensions()
            self.extension_manager.load_extensions()
            self.extension_manager.initialize_extensions()
            self.lang.load_extension_languages(self.extension_manager)
    
        # --- Args Manager (needs ExtensionManager to be ready) ---
        self.args_manager = ArgsManager(self)

        # If we are only running for args, don't build the whole UI yet.
        if not run_gui:
            return

        self.setup_ui()

    def setup_ui(self):
        """Completes the UI initialization. Called after arg processing."""
        # --- UI Creation ---

        self.init_ui()

        # --- Context Menu and Key Manager need UI elements to exist first ---
        self.context_menu_manager = ContextMenuManager(self)
        self.key_manager = KeyManager(self)

        # --- Final Setup ---
        self.context_menu_manager.setup()
        self.key_manager.setup_shortcuts()
        self.load_all_settings()
        self.retranslate_ui()
        
        # --- Ignore Lists State ---
        self.temp_ignore_dirs = []
        self.temp_ignore_files = []
        
        # Connect extensions to UI managers
        self.extension_manager.connect_ui_extensions(self.key_manager, self.context_menu_manager)
    
    def closeEvent(self, event):
        """Ensures all detached tabs are closed when the main window closes."""
        if hasattr(self, 'detached_tabs'):
            for data in list(self.detached_tabs.values()):
                if not data['window'].isHidden():
                    data['window'].close()
        super().closeEvent(event)

    def init_ui(self):
        """Initializes the main UI structure by calling helper methods."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_layout = QStackedLayout(central_widget)
    
        # Create the main content widget (layer 0)
        main_content_widget = QWidget()
        main_layout = QVBoxLayout(main_content_widget)
    
        top_bar = self._create_top_bar()
        main_tabs = self._create_main_tabs()
        
        main_layout.addLayout(top_bar)
        main_layout.addWidget(main_tabs)
    
        # Create the settings overlay (layer 1)
        self.settings_panel = SettingsPanel(self)
        self.settings_panel.closed.connect(self.toggle_settings_panel)
    
        # Add widgets to the stacked layout
        self.stacked_layout.addWidget(main_content_widget) # Index 0
        self.stacked_layout.addWidget(self.settings_panel) # Index 1
        self.stacked_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.stacked_layout.setCurrentIndex(0)
    
    def _create_top_bar(self):
        """Creates the top bar with project selection and global buttons."""
        top_bar_layout = QHBoxLayout()
        project_panel = QFrame()
        project_panel.setFrameShape(QFrame.Shape.StyledPanel)
        project_layout = QHBoxLayout(project_panel)
        self.select_folder_button = QPushButton()
        self.select_folder_button.clicked.connect(self.select_project_folder)
        self.path_label = QLabel()
        self.edit_ignore_list_button = QPushButton()
        self.edit_ignore_list_button.clicked.connect(self.open_ignore_settings)
        self.edit_ignore_list_button.setEnabled(False) # Disabled by default
        
        project_layout.addWidget(self.select_folder_button)
        project_layout.addWidget(self.path_label, stretch=1)
        project_layout.addWidget(self.edit_ignore_list_button)
        
        top_bar_layout.addWidget(project_panel, stretch=1)
    
        self.settings_button = QPushButton()
        self.settings_button.setIcon(svg_to_icon(get_svg_content(ICON_MAIN_SETTINGS)))
        self.settings_button.clicked.connect(self.toggle_settings_panel)
        self.restart_button = QPushButton()
        self.restart_button.clicked.connect(self.restart_application)
        self.settings_button.addGUITooltip(self.lang.get('settings_tooltip'))
        self.restart_button.addGUITooltip(self.lang.get('restart_tooltip'))
    
        # Home Button (if launched via Launcher)
        if self.on_home_callback:
            self.home_button = QPushButton()
            self.home_button.setIcon(svg_to_icon(get_svg_content(ICON_HOME), "#cccccc"))
            self.home_button.setProperty("no_custom_tooltip", True)
            self.home_button.setToolTip(self.lang.get('home_tooltip'))
            self.home_button.clicked.connect(self.go_home)
            top_bar_layout.addWidget(self.home_button)
    
        top_bar_layout.addWidget(self.settings_button)
        top_bar_layout.addWidget(self.restart_button)
        return top_bar_layout
        
    def go_home(self):
        self.close()
        if self.on_home_callback:
            self.on_home_callback()
    
    def _create_main_tabs(self):
        """Creates and populates the main QTabWidget using the extension manager."""
        self.tab_widget = QTabWidget()
        
        # This is needed for the dev patcher tab, so it's created here
        self.patcher_log_output = LogBox(self)

        # Define the desired order for the tabs
        tab_order = ['dev_patcher', 'project_text_packer', 'project_launcher']
        
        # Get all available widgets from the extension manager and store them in a dict for easy lookup
        extension_widgets = dict(self.extension_manager.get_extension_widgets())
        
        # Add tabs in the specified order
        for name in tab_order:
            if name in extension_widgets:
                widget_class = extension_widgets.pop(name)
                tab_widget_instance = widget_class(self)
                index = self.tab_widget.addTab(tab_widget_instance, self.lang.get(f'{name}_tab'))
                self.tabs[name] = tab_widget_instance
                self._add_detach_button(index, name)

        # Add remaining extensions
        for name in sorted(extension_widgets.keys()):
            widget_class = extension_widgets[name]
            tab_widget_instance = widget_class(self)
            tab_title = self.lang.get(f'{name}_tab')
            if tab_title == f'{name}_tab':
                tab_title = name.replace('_', ' ').title()
            index = self.tab_widget.addTab(tab_widget_instance, tab_title)
            self.tabs[name] = tab_widget_instance
            self._add_detach_button(index, name)
        
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        return self.tab_widget
    
    def _add_detach_button(self, index, name):
        btn = QPushButton()
        btn.setIcon(svg_to_icon(get_svg_content(ICON_DETACH), "#888"))
        btn.setProperty("no_custom_tooltip", True)
        btn.setToolTip(self.lang.get('detach_tab_tooltip'))
        btn.setFixedSize(24, 24)
        btn.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background-color: rgba(128, 128, 128, 0.3); }")
        btn.clicked.connect(lambda: self.detach_tab(name))
        self.tab_widget.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, btn)
    
    def detach_tab(self, name):
        widget = self.tabs.get(name)
        if not widget: return
    
        index = self.tab_widget.indexOf(widget)
        if index == -1: return
    
        title = self.tab_widget.tabText(index)
        self.tab_widget.removeTab(index)
    
        if not hasattr(self, 'detached_tabs'):
            self.detached_tabs = {}
    
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        msg_label = QLabel(self.lang.get('tab_detached_msg'))
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setStyleSheet("font-size: 14pt; color: #888;")
    
        restore_btn = QPushButton(self.lang.get('restore_tab_btn'))
        restore_btn.setFixedSize(150, 40)
        restore_btn.setStyleSheet("font-size: 12pt;")
        restore_btn.clicked.connect(lambda: self.attach_tab(name))
    
        layout.addStretch()
        layout.addWidget(msg_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(restore_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
    
        new_index = self.tab_widget.insertTab(index, placeholder, title)
        self.tab_widget.setCurrentIndex(new_index)
    
        detached_win = DetachedTabWindow(self, widget, name, title)
        detached_win.show()
    
        self.detached_tabs[name] = {
            'placeholder': placeholder,
            'window': detached_win
        }
    
    def attach_tab(self, name):
        if not hasattr(self, 'detached_tabs') or name not in self.detached_tabs:
            return
    
        data = self.detached_tabs[name]
        placeholder = data['placeholder']
        detached_win = data['window']
        widget = self.tabs.get(name)
    
        index = self.tab_widget.indexOf(placeholder)
        if index != -1:
            title = self.tab_widget.tabText(index)
            self.tab_widget.removeTab(index)
            new_index = self.tab_widget.insertTab(index, widget, title)
            self._add_detach_button(new_index, name)
            self.tab_widget.setCurrentIndex(new_index)
    
        del self.detached_tabs[name]
    
        if not detached_win.isHidden():
            detached_win.close()
    
    
    def on_tab_changed(self, index):
        """Triggers actions when the user switches tabs."""
        # This needs to be more generic now
        current_widget = self.tab_widget.widget(index)
        if hasattr(current_widget, 'project_folder_changed'):
             if self.root_path:
                current_widget.project_folder_changed(self.root_path)

    def open_ignore_settings(self):
        """Opens the dialog to edit ignore lists."""
        try:
            # This is a core quick setting, so we import it directly
            from systems.settings.gui.quick import get_quick_settings

            qs_defs = get_quick_settings()
            ignore_list_def = next((item for item in qs_defs if item.get('id') == 'core_ignore_list'), None)
    
            if ignore_list_def and ignore_list_def['qs_type'] == 'window':
                DialogClass = ignore_list_def['widget_class']
                dialog = DialogClass(self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Error", "Could not find 'Ignore Lists' quick setting definition.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open ignore settings: {e}")
    
    def get_combined_ignore_lists(self):
        """
        Aggregates Global settings, Temporary session lists, and .gitignore (if enabled).
        Returns: (combined_dirs, combined_files)
        """
        # 1. Global
        global_dirs, global_files, use_gitignore = self.settings_manager.get_ignore_lists()
    
        # 2. Temporary
        combined_dirs = set(global_dirs + self.temp_ignore_dirs)
        combined_files = set(global_files + self.temp_ignore_files)
    
        # 3. .gitignore
        if use_gitignore and self.root_path:
            git_dirs, git_files = IgnoreHandler.parse_gitignore(self.root_path)
            combined_dirs.update(git_dirs)
            combined_files.update(git_files)
    
        return list(combined_dirs), list(combined_files)
    
    
    def apply_main_settings(self, settings: dict):
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
    
        # Redraw and re-translate the entire UI
        self.retranslate_ui()

    def retranslate_ui(self):
        """Applies all translations to the UI elements."""
        self.setWindowTitle(self.lang.get('window_title'))
        
        # Get theme colors early so they're available throughout the method
        p = self.theme_manager.current_palette
        icon_def = p.get("icon_default", "#e0e0e0")
        icon_dim = p.get("icon_dim", "#888888")
        
        self.select_folder_button.setText(self.lang.get('select_project_folder_btn'))
        self.edit_ignore_list_button.setText(self.lang.get('edit_ignore_list_btn'))
        if self.edit_ignore_list_button.isEnabled():
            self.edit_ignore_list_button.addGUITooltip(self.lang.get('edit_ignore_list_tooltip'))
        else:
            self.edit_ignore_list_button.addGUITooltip(self.lang.get('edit_ignore_list_disabled_tooltip'))

        if self.root_path:
             self.path_label.setText(self.lang.get('project_path_label_selected').format(self.root_path))
        else:
             self.path_label.setText(self.lang.get('project_path_label_unselected'))

        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            # Find the name based on the widget instance
            name = next((k for k, v in self.tabs.items() if v == widget), None)
            if name:
                self.tab_widget.setTabText(i, self.lang.get(f'{name}_tab'))

            # Update detach button tooltip and icon color
            btn = self.tab_widget.tabBar().tabButton(i, QTabBar.ButtonPosition.RightSide)
            if btn:
                btn.setIcon(svg_to_icon(get_svg_content(ICON_DETACH), icon_dim))
                btn.setToolTip(self.lang.get('detach_tab_tooltip'))

        if hasattr(self, 'detached_tabs'):
            for name, data in self.detached_tabs.items():
                win = data['window']
                placeholder = data['placeholder']
                tab_title = self.lang.get(f'{name}_tab')
                if tab_title == f'{name}_tab':
                    tab_title = name.replace('_', ' ').title()
                win.setWindowTitle(tab_title)
        
                msg_label = placeholder.findChild(QLabel)
                if msg_label:
                    msg_label.setText(self.lang.get('tab_detached_msg'))
        
                restore_btn = placeholder.findChild(QPushButton)
                if restore_btn:
                    restore_btn.setText(self.lang.get('restore_tab_btn'))

        self.settings_button.setIcon(svg_to_icon(get_svg_content(ICON_MAIN_SETTINGS), icon_def))
        self.settings_button.setText(self.lang.get('settings_btn')).addGUITooltip(self.lang.get('settings_tooltip'))
        self.restart_button.setText(self.lang.get('restart_btn')).addGUITooltip(self.lang.get('restart_tooltip'))
        self.select_folder_button.setText(self.lang.get('select_project_folder_btn')).addGUITooltip(self.lang.get('select_project_folder_tooltip'))
        self.edit_ignore_list_button.setText(self.lang.get('edit_ignore_list_btn'))

        if hasattr(self, 'home_button'):
            self.home_button.setIcon(svg_to_icon(get_svg_content(ICON_HOME), icon_dim))
            self.home_button.setToolTip(self.lang.get('home_tooltip'))

        self.patcher_log_output.setPlaceholderText(self.lang.get('patcher_log_placeholder'))
        self.patcher_log_output.setToolTip(self.lang.get('patcher_log_placeholder'))

        # Retranslate all tabs
        for tab in self.tabs.values():
            if hasattr(tab, 'retranslate_ui'):
                tab.retranslate_ui()
        
        if hasattr(self, 'settings_panel'):
            self.settings_panel.retranslate_ui()

    def load_all_settings(self):
        # The new system loads all settings at once.
        # Applying them is handled by individual components or panels.
        settings = self.settings_manager.load_settings_file()
        core_settings = settings.get('core', {})
    
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

        ui_settings = core_settings.get('ui', {})
        app = QApplication.instance()
        if hasattr(app, '_tooltip_enhancer'):
            app._tooltip_enhancer.always_show = ui_settings.get('always_show_tooltips', False)

    
        # Settings for tabs are loaded by the tabs themselves when they are created
        # or when settings panel is opened.
        self.patcher_log_output.appendPlainText(self.lang.get('settings_loaded_log'))

    def toggle_settings_panel(self):
        current_index = self.stacked_layout.currentIndex()
        if current_index == 0:
            self.settings_panel.store_initial_state()
            self.stacked_layout.setCurrentIndex(1)
        else:
            self.stacked_layout.setCurrentIndex(0)

    def restart_application(self):
        reply = QMessageBox.question(
            self, self.lang.get('restart_dialog_title'), self.lang.get('restart_dialog_msg'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.patcher_log_output.appendPlainText(self.lang.get('restart_signal_sent_log'))
            QApplication.exit(RESTART_CODE)

    def select_project_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.lang.get('select_project_folder_btn'))
        if folder_path:
            self.root_path = os.path.normpath(folder_path)
            self.path_label.setText(self.lang.get('project_path_label_selected').format(self.root_path))
            self.edit_ignore_list_button.setEnabled(True)
            self.theme_manager.update_path_label_style()
            self.patcher_log_output.appendPlainText(self.lang.get('project_folder_selected_log').format(self.root_path))
            
            # Notify all tabs that the folder has changed
            for tab in self.tabs.values():
                if hasattr(tab, 'project_folder_changed'):
                    tab.project_folder_changed(self.root_path)