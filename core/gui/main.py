from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QApplication, QFileDialog, QLabel,
        QMessageBox,
            QFrame, QStackedLayout, QTabWidget, QTabBar, QSizePolicy, QGridLayout
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
from systems.project.bookmarks import BookmarksDialog
from PySide6.QtWidgets import QComboBox, QStylePainter, QStyleOptionComboBox, QStyle
from PySide6.QtWidgets import QToolTip
from PySide6.QtGui import QCursor
from systems.gui.icons import IconManager

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



class PathDisplayWidget(QFrame):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(100)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

        self.full_label = QLabel()
        self.full_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.full_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.full_label.setMinimumWidth(1)

        self.root_btn = QPushButton("@ROOT")
        self.root_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.root_btn.setProperty("no_custom_tooltip", True)
        self.root_btn.clicked.connect(self._copy_root)

        self._btn_style = (
            "QPushButton {{ border: 1px solid #555; background: transparent; "
            "border-radius: 4px; padding: 2px 6px; font-weight: bold; color: {color}; }}\n"
            "QPushButton:hover {{ background: rgba(128, 128, 128, 0.2); }}"
        )

        self._layout.addWidget(self.full_label, 1)
        self._layout.addWidget(self.root_btn)

        self._full_text = ""
        self.root_btn.hide()

    def setText(self, text):
        self._full_text = text
        self._check_fit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._check_fit()

    def _check_fit(self):
        r_path = getattr(self.main_window, 'root_path', '')
        ws_path = getattr(self.main_window, 'workspace_path', '')

        has_path = bool(r_path) or bool(ws_path)

        if not has_path:
            self.full_label.setText(self._full_text)
            self.full_label.setToolTip("")
            self.root_btn.hide()
            return

        self.root_btn.show()

        path_to_show = r_path if r_path else ws_path
        self.root_btn.setToolTip(path_to_show)

        fm = self.full_label.fontMetrics()
        available_width = self.width() - self.root_btn.width() - self._layout.spacing() - 5

        import re
        plain_text = re.sub(r'<[^>]+>', '', self._full_text)

        if fm.horizontalAdvance(plain_text) > available_width and available_width > 0:
            elided = fm.elidedText(plain_text, Qt.TextElideMode.ElideRight, available_width)
            self.full_label.setText(elided)
            self.full_label.setToolTip(plain_text)
        else:
            self.full_label.setText(self._full_text)
            self.full_label.setToolTip("")

    def _copy_root(self):
        path = getattr(self.main_window, 'root_path', '') or getattr(self.main_window, 'workspace_path', '')
        if path:
            QApplication.clipboard().setText(path)
            msg = self.main_window.lang.get('doc_copied_tooltip', 'Copied!')
            QToolTip.showText(QCursor.pos(), f"{msg}\n{path}", self.root_btn)

    def setStyleSheet(self, style):
        color = "#29b8db"
        import re
        m = re.search(r'color:\s*(#[0-9a-fA-F]+)', style)
        if m:
            color = m.group(1)

        btn_style = self._btn_style.format(color=color)
        self.root_btn.setStyleSheet(btn_style)
        self.full_label.setStyleSheet(style)


class WorkspaceProjectComboBox(QComboBox):
    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        text = opt.currentText
        max_len = 16
        if len(text) > max_len:
            opt.currentText = text[:max_len-3] + "..."

        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt)
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opt)

class MainWindow(QMainWindow):
    def __init__(self, run_gui=True, context=None, on_home=None):
        super().__init__()
    
        self.root_path = None
        
        self.current_mode = 'Project'
        self.workspace_path = None
        
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
        """Creates the top bar with project selection and global buttons structured in distinct blocks."""
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 5)
        top_bar_layout.setSpacing(10)

        block_style = """
            QFrame#TopBarBlock {
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 6px;
                background-color: rgba(128, 128, 128, 0.05);
            }
        """

        # --- LEFT BLOCK ---
        left_block = QFrame()
        left_block.setObjectName("TopBarBlock")
        left_block.setStyleSheet(block_style)
        left_layout = QVBoxLayout(left_block)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(6)

        self.bookmarks_button = QPushButton()
        self.bookmarks_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.bookmarks_button.clicked.connect(self.open_bookmarks)

        self.edit_ignore_list_button = QPushButton()
        self.edit_ignore_list_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.edit_ignore_list_button.clicked.connect(self.open_ignore_settings)
        self.edit_ignore_list_button.setEnabled(False)

        left_layout.addWidget(self.bookmarks_button)
        left_layout.addWidget(self.edit_ignore_list_button)

        # --- CENTER BLOCK ---
        center_block = QFrame()
        center_block.setObjectName("TopBarBlock")
        center_block.setStyleSheet(block_style)
        center_layout = QVBoxLayout(center_block)
        center_layout.setContentsMargins(6, 6, 6, 6)
        center_layout.setSpacing(6)

        center_row1 = QHBoxLayout()

        mode_vlayout = QVBoxLayout()
        mode_vlayout.setSpacing(2)
        self.mode_label = QLabel(self.lang.get('mode_label', 'Mode:'))
        self.mode_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Project", "Workspace"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_vlayout.addWidget(self.mode_label)
        mode_vlayout.addWidget(self.mode_combo)
        mode_vlayout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.workspace_controls_widget = QWidget()
        ws_layout = QHBoxLayout(self.workspace_controls_widget)
        ws_layout.setContentsMargins(0, 0, 0, 0)
        ws_layout.setSpacing(6)

        ws_combo_vlayout = QVBoxLayout()
        ws_combo_vlayout.setSpacing(2)
        self.ws_project_list_label = QLabel(self.lang.get('project_list_label', 'Project List:'))
        self.ws_project_list_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        self.workspace_project_combo = WorkspaceProjectComboBox()
        self.workspace_project_combo.currentTextChanged.connect(self.on_workspace_project_changed)
        ws_combo_vlayout.addWidget(self.ws_project_list_label)
        ws_combo_vlayout.addWidget(self.workspace_project_combo)

        self.ws_add_btn = QPushButton()
        self.ws_add_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.ws_add_btn.setProperty("no_custom_tooltip", True)
        self.ws_add_btn.clicked.connect(self._add_workspace_project)

        self.ws_edit_btn = QPushButton()
        self.ws_edit_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.ws_edit_btn.setProperty("no_custom_tooltip", True)
        self.ws_edit_btn.clicked.connect(self._edit_workspace_projects)

        self.ws_refresh_btn = QPushButton()
        self.ws_refresh_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.ws_refresh_btn.setProperty("no_custom_tooltip", True)
        self.ws_refresh_btn.clicked.connect(self._scan_workspace)

        ws_layout.addLayout(ws_combo_vlayout, stretch=1)
        ws_layout.addWidget(self.ws_add_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        ws_layout.addWidget(self.ws_edit_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        ws_layout.addWidget(self.ws_refresh_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        self.workspace_controls_widget.setVisible(False)

        center_row1.addLayout(mode_vlayout)
        center_row1.addWidget(self.workspace_controls_widget, stretch=1)
        center_row1.addStretch()

        center_row2 = QHBoxLayout()
        self.select_folder_button = QPushButton()
        self.select_folder_button.clicked.connect(self.select_project_folder)

        self.path_label = PathDisplayWidget(self)

        center_row2.addWidget(self.select_folder_button)
        center_row2.addWidget(self.path_label, stretch=1)

        center_layout.addLayout(center_row1)
        center_layout.addLayout(center_row2)

        # --- RIGHT BLOCK ---
        right_block = QFrame()
        right_block.setObjectName("TopBarBlock")
        right_block.setStyleSheet(block_style)
        right_layout = QGridLayout(right_block)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(6)

        if self.on_home_callback:
            self.home_button = QPushButton()
            self.home_button.setIcon(IconManager.get_icon("core.home", "#cccccc"))
            self.home_button.setToolTip(self.lang.get('home_tooltip'))
            self.home_button.clicked.connect(self.go_home)
            self.home_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            right_layout.addWidget(self.home_button, 0, 0)

        self.restart_button = QPushButton()
        self.restart_button.clicked.connect(self.restart_application)
        self.restart_button.addGUITooltip(self.lang.get('restart_tooltip'))
        self.restart_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        if self.on_home_callback:
            right_layout.addWidget(self.restart_button, 0, 1)
        else:
            right_layout.addWidget(self.restart_button, 0, 0, 1, 2)

        self.ext_button = QPushButton()
        self.ext_button.setIcon(IconManager.get_icon("core.extensions"))
        self.ext_button.clicked.connect(self.open_extensions)
        self.ext_button.addGUITooltip(self.lang.get('launcher_ext_tooltip'))
        self.ext_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        right_layout.addWidget(self.ext_button, 1, 0)

        self.settings_button = QPushButton()
        self.settings_button.setIcon(IconManager.get_icon("core.main_settings"))
        self.settings_button.clicked.connect(self.toggle_settings_panel)
        self.settings_button.addGUITooltip(self.lang.get('settings_tooltip'))
        self.settings_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        right_layout.addWidget(self.settings_button, 1, 1)

        right_layout.setColumnStretch(0, 1)
        right_layout.setColumnStretch(1, 1)

        top_bar_layout.addWidget(left_block)
        top_bar_layout.addWidget(center_block, stretch=1)
        top_bar_layout.addWidget(right_block)

        return top_bar_layout
        
    def go_home(self):
        self.hide()
        if self.on_home_callback:
            self.on_home_callback()

    def open_extensions(self):
        from core.gui.launch import ExtensionsWindow
        dialog = ExtensionsWindow(self)
        dialog.exec()


    def _add_workspace_project(self):
        if self.current_mode != 'Workspace' or not self.workspace_path:
            return
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        name, ok = QInputDialog.getText(
            self, 
            self.lang.get('add_workspace_project_title', 'Add new workspace project'), 
            self.lang.get('add_workspace_project_prompt', 'Enter name for new project in workspace folder:')
        )
        if ok and name.strip():
            new_path = os.path.join(self.workspace_path, name.strip())
            if not os.path.exists(new_path):
                try:
                    os.makedirs(new_path, exist_ok=True)
                    self._scan_workspace()
                    idx = self.workspace_project_combo.findText(name.strip())
                    if idx >= 0:
                        self.workspace_project_combo.setCurrentIndex(idx)
                except Exception as e:
                    QMessageBox.warning(self, self.lang.get('patch_load_error_title', 'Error'), f"Could not create project folder: {e}")
            else:
                QMessageBox.warning(self, self.lang.get('patch_load_error_title', 'Error'), "A folder with this name already exists.")

    def _edit_workspace_projects(self):
        if self.current_mode != 'Workspace' or not self.workspace_path:
            return
        from systems.project.workspace_dialogs import WorkspaceProjectsDialog
        dialog = WorkspaceProjectsDialog(self)
        dialog.exec()
        self._scan_workspace()
        if self.root_path:
            idx = self.workspace_project_combo.findText(os.path.basename(self.root_path))
            if idx >= 0:
                self.workspace_project_combo.setCurrentIndex(idx)
            else:
                self.root_path = None
                self.theme_manager.update_path_label_style()


    
    def reload_tabs(self):
        """Adds tabs for newly enabled extensions and removes tabs for disabled ones."""
        extension_widgets = dict(self.extension_manager.get_extension_widgets())

        # 1. Remove tabs for extensions that are no longer enabled
        for name in list(self.tabs.keys()):
            if name not in extension_widgets:
                widget = self.tabs[name]

                # If detached, re-attach first to cleanly remove
                if hasattr(self, 'detached_tabs') and name in self.detached_tabs:
                    self.attach_tab(name)

                index = self.tab_widget.indexOf(widget)
                if index != -1:
                    self.tab_widget.removeTab(index)

                widget.deleteLater()
                del self.tabs[name]

        # 2. Add tabs for newly enabled extensions
        tab_order = ['dev_patcher', 'project_text_packer', 'project_launcher']

        newly_added =[]
        for name in tab_order:
            if name in extension_widgets and name not in self.tabs:
                widget_class = extension_widgets[name]
                tab_widget_instance = widget_class(self)
                index = self.tab_widget.addTab(tab_widget_instance, self.lang.get(f'{name}_tab'))
                self.tabs[name] = tab_widget_instance
                self._add_detach_button(index, name)
                if hasattr(tab_widget_instance, 'project_folder_changed') and self.root_path:
                    tab_widget_instance.project_folder_changed(self.root_path)
                newly_added.append(name)

        for name in sorted(extension_widgets.keys()):
            if name not in tab_order and name not in self.tabs:
                widget_class = extension_widgets[name]
                tab_widget_instance = widget_class(self)
                tab_title = self.lang.get(f'{name}_tab')
                if tab_title == f'{name}_tab':
                    tab_title = name.replace('_', ' ').title()
                index = self.tab_widget.addTab(tab_widget_instance, tab_title)
                self.tabs[name] = tab_widget_instance
                self._add_detach_button(index, name)
                if hasattr(tab_widget_instance, 'project_folder_changed') and self.root_path:
                    tab_widget_instance.project_folder_changed(self.root_path)
                newly_added.append(name)

        # Register hooks for newly added tabs
        for name in newly_added:
            meta = self.extension_manager.extensions[name]
            self.extension_manager.comp_loader.register_ui_hooks(meta, self.key_manager, self.context_menu_manager)

        self.retranslate_ui()

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
        btn.setIcon(IconManager.get_icon("core.detach", "#888"))
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
        Aggregates Global settings, Project settings, Temporary session lists, and .gitignore.
        Returns: (combined_dirs, combined_files)
        """
        # 1. Global & Project
        g_dirs, g_files, use_gitignore, p_dirs, p_files = self.settings_manager.get_ignore_lists()

        # 2. Temporary & Combined
        combined_dirs = set(g_dirs + p_dirs + self.temp_ignore_dirs)
        combined_files = set(g_files + p_files + self.temp_ignore_files)
    
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
            if 'ui' in settings:
                app = QApplication.instance()
                if hasattr(app, '_tooltip_enhancer'):
                    app._tooltip_enhancer.always_show = settings['ui'].get('always_show_tooltips', False)

                font_size = settings['ui'].get('font_size', 10)
                font = app.font()
                font.setPointSize(font_size)
                app.setFont(font)

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
        
        if self.current_mode == 'Workspace':
            self.select_folder_button.setText(self.lang.get('select_workspace_folder_btn', 'Select Workspace Folder...'))
            if hasattr(self.select_folder_button, 'addGUITooltip'):
                self.select_folder_button.addGUITooltip(self.lang.get('select_workspace_folder_tooltip', 'Select a workspace folder containing multiple projects.'))
        else:
            self.select_folder_button.setText(self.lang.get('select_project_folder_btn'))
            if hasattr(self.select_folder_button, 'addGUITooltip'):
                self.select_folder_button.addGUITooltip(self.lang.get('select_project_folder_tooltip'))

        self.mode_combo.setItemText(0, self.lang.get('mode_project', 'Project'))
        self.mode_combo.setItemText(1, self.lang.get('mode_workspace', 'Workspace'))
        if hasattr(self, 'mode_label'):
            self.mode_label.setText(self.lang.get('mode_label', 'Mode:')).addGUITooltip(self.lang.get('mode_label_tooltip', 'Switch between Project and Workspace modes.'))
        if hasattr(self, 'ws_project_list_label'):
            self.ws_project_list_label.setText(self.lang.get('project_list_label', 'Project List:')).addGUITooltip(self.lang.get('project_list_label_tooltip', 'Select a project from the current workspace.'))
        self.bookmarks_button.addGUITooltip(self.lang.get('bookmarks_title', 'Project Bookmarks'))

        self.ws_add_btn.setToolTip(self.lang.get('workspace_add_project_tooltip', 'Add new project to workspace'))
        self.ws_edit_btn.setToolTip(self.lang.get('workspace_edit_projects_tooltip', 'Edit workspace projects'))
        self.ws_refresh_btn.setToolTip(self.lang.get('workspace_refresh_tooltip', 'Refresh workspace projects'))
        self.ws_add_btn.setIcon(IconManager.get_icon("core.plus", icon_def))
        self.ws_edit_btn.setIcon(IconManager.get_icon("core.edit", icon_def))
        self.ws_refresh_btn.setIcon(IconManager.get_icon("dev_patcher.refresh", icon_def))

        self.edit_ignore_list_button.setText(self.lang.get('edit_ignore_list_btn'))
        if self.edit_ignore_list_button.isEnabled():
            self.edit_ignore_list_button.addGUITooltip(self.lang.get('edit_ignore_list_tooltip'))
        else:
            self.edit_ignore_list_button.addGUITooltip(self.lang.get('edit_ignore_list_disabled_tooltip'))

        if self.current_mode == 'Workspace' and self.workspace_path:
             self.path_label.setText(self.lang.get('workspace_label', 'Workspace: {}').format(self.workspace_path))
        elif self.root_path:
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
                btn.setIcon(IconManager.get_icon("core.detach", icon_dim))
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

        self.bookmarks_button.setIcon(IconManager.get_icon("core.bookmarks", icon_def))
        self.ext_button.setIcon(IconManager.get_icon("core.extensions", icon_def))
        self.ext_button.setText(self.lang.get('launcher_btn_ext')).addGUITooltip(self.lang.get('launcher_ext_tooltip'))

        self.settings_button.setIcon(IconManager.get_icon("core.main_settings", icon_def))
        self.settings_button.setText(self.lang.get('settings_btn')).addGUITooltip(self.lang.get('settings_tooltip'))

        self.restart_button.setIcon(IconManager.get_icon("core.restart", icon_def))
        self.restart_button.setText(self.lang.get('restart_btn')).addGUITooltip(self.lang.get('restart_tooltip'))
        self.edit_ignore_list_button.setText(self.lang.get('edit_ignore_list_btn'))

        if hasattr(self, 'home_button'):
            self.home_button.setIcon(IconManager.get_icon("core.home", icon_dim))
            self.home_button.addGUITooltip(self.lang.get('home_tooltip'))

        self.patcher_log_output.setPlaceholderText(self.lang.get('patcher_log_placeholder'))
        self.patcher_log_output.setToolTip(self.lang.get('patcher_log_placeholder'))

        # Retranslate all tabs
        for tab in self.tabs.values():
            if hasattr(tab, 'retranslate_ui'):
                tab.retranslate_ui()
        
        if hasattr(self, 'settings_panel'):
            self.settings_panel.retranslate_ui()

        # Equalize button widths in the right block
        buttons = [self.restart_button, self.ext_button, self.settings_button]
        if hasattr(self, 'home_button'):
            buttons.append(self.home_button)

        max_width = 0
        for btn in buttons:
            # Force a polish to get an updated sizeHint after text/icon changes
            btn.style().polish(btn)
            max_width = max(max_width, btn.sizeHint().width())

        for btn in buttons:
            btn.setMinimumWidth(max_width)


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
        ui_settings = core_settings.get('ui', {})
        app = QApplication.instance()
        if hasattr(app, '_tooltip_enhancer'):
            app._tooltip_enhancer.always_show = ui_settings.get('always_show_tooltips', False)

        font_size = ui_settings.get('font_size', 10)
        font = app.font()
        font.setPointSize(font_size)
        app.setFont(font)

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

    def _apply_project_change(self):
        self.settings_manager.set_project_path(self.root_path)
        self.load_all_settings()
        self.extension_manager.reload_extensions()

        # Notify all tabs that the folder has changed
        for tab in self.tabs.values():
            if hasattr(tab, 'project_folder_changed'):
                tab.project_folder_changed(self.root_path)

    def select_project_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.lang.get('select_project_folder_btn'))
        if folder_path:
            folder_path = os.path.normpath(folder_path)

            if self.current_mode == 'Project':
                self.root_path = folder_path
                self.workspace_path = None
                self.path_label.setText(self.lang.get('project_path_label_selected').format(self.root_path))
                self.workspace_controls_widget.setVisible(False)
            else:
                self.workspace_path = folder_path
                self.path_label.setText(self.lang.get('workspace_label', 'Workspace: {}').format(self.workspace_path))
                self.workspace_controls_widget.setVisible(True)
                self._scan_workspace()
                if self.workspace_project_combo.count() > 0:
                    self.root_path = os.path.join(self.workspace_path, self.workspace_project_combo.currentText())
                else:
                    self.root_path = None

            self.edit_ignore_list_button.setEnabled(True)
            self.theme_manager.update_path_label_style()
            self.patcher_log_output.appendPlainText(self.lang.get('project_folder_selected_log').format(self.root_path or self.workspace_path))
            self._apply_project_change()

    def on_mode_changed(self, mode):
        old_mode = self.current_mode
        self.current_mode = mode
        if old_mode == mode: return

        if mode == 'Workspace':
            self.mode_combo.setItemText(0, self.lang.get('mode_project', 'Project'))
            self.mode_combo.setItemText(1, self.lang.get('mode_workspace', 'Workspace'))
            self.workspace_controls_widget.setVisible(True)

            if old_mode == 'Project' and self.root_path:
                QMessageBox.warning(
                    self,
                    self.lang.get('mode_switch_warning_title', "Mode Switched"),
                    self.lang.get('mode_switch_to_workspace_msg', 
                        "You switched to Workspace mode, but a Project folder is currently selected.\n"
                        "Please select a valid Workspace folder, or switch back to Project mode.")
                )
                self.workspace_path = os.path.dirname(self.root_path)
                self.path_label.setText(self.lang.get('workspace_label', 'Workspace: {}').format(self.workspace_path))
                self._scan_workspace()
                idx = self.workspace_project_combo.findText(os.path.basename(self.root_path))
                if idx >= 0:
                    self.workspace_project_combo.setCurrentIndex(idx)
            elif self.root_path and not self.workspace_path:
                self.workspace_path = os.path.dirname(self.root_path)
                self.path_label.setText(self.lang.get('workspace_label', 'Workspace: {}').format(self.workspace_path))
                self._scan_workspace()
                idx = self.workspace_project_combo.findText(os.path.basename(self.root_path))
                if idx >= 0:
                    self.workspace_project_combo.setCurrentIndex(idx)

        else: # mode == 'Project'
            self.workspace_controls_widget.setVisible(False)
            if old_mode == 'Workspace' and self.root_path:
                QMessageBox.information(
                    self,
                    self.lang.get('mode_switch_warning_title', "Mode Switched"),
                    self.lang.get('mode_switch_to_project_msg', 
                        f"You switched from Workspace to Project mode.\n"
                        f"The current project path will be set to:\n{self.root_path}\n"
                        "You can change the project folder if needed.")
                )
                self.path_label.setText(self.lang.get('project_path_label_selected').format(self.root_path))
            elif self.root_path:
                self.path_label.setText(self.lang.get('project_path_label_selected').format(self.root_path))

        self.retranslate_ui()

    def on_workspace_project_changed(self, project_name):
        if self.current_mode == 'Workspace' and self.workspace_path and project_name:
            potential_path = os.path.join(self.workspace_path, project_name)
            if os.path.isdir(potential_path):
                self.root_path = potential_path
                self.theme_manager.update_path_label_style()
                self._apply_project_change()

    def _scan_workspace(self):
        self.workspace_project_combo.blockSignals(True)
        self.workspace_project_combo.clear()
        if self.workspace_path and os.path.isdir(self.workspace_path):
            dirs =[d for d in os.listdir(self.workspace_path)
                    if os.path.isdir(os.path.join(self.workspace_path, d)) and not d.startswith('.')]
            sorted_dirs = sorted(dirs)
            self.workspace_project_combo.addItems(sorted_dirs)

            max_width = 0
            fm = self.workspace_project_combo.fontMetrics()
            for d in sorted_dirs:
                width = fm.horizontalAdvance(d)
                if width > max_width: max_width = width

            # Add padding to prevent horizontal scrollbar where unnecessary 
            self.workspace_project_combo.view().setMinimumWidth(max_width + 40)

        self.workspace_project_combo.blockSignals(False)

    def open_bookmarks(self):
        dialog = BookmarksDialog(self)
        dialog.exec()