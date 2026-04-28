import tomllib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QCheckBox,
    QSpacerItem, QSizePolicy, QFormLayout, QScrollArea, QPushButton, QFrame
)
from systems.settings.defaults import main_default_settings

class ExtensionManagerWidget(QWidget):
    def __init__(self, extensions_window):
        super().__init__()
        self.extensions_window = extensions_window
        self.main_window = extensions_window.main_window
        self.lang = self.main_window.lang
        self.extension_manager = self.main_window.extension_manager
        self.settings_manager = self.main_window.settings_manager
        self.checkboxes = {}
        self.settings_widgets = {}
        self.defaults = main_default_settings

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        # Create container widget for scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 5, 0, 0)

        self.core_group = QGroupBox()
        self.core_layout = QVBoxLayout(self.core_group)
        container_layout.addWidget(self.core_group)

        self.custom_group = QGroupBox()
        self.custom_layout = QVBoxLayout(self.custom_group)
        container_layout.addWidget(self.custom_group)

        container_layout.addStretch()

        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        self.populate_extensions()
        self.retranslate_ui()

    def populate_extensions(self):
        core_extensions_exist = False
        custom_extensions_exist = False

        for name, meta in self.extension_manager.extensions.items():
            ext_widget = self._create_extension_widget(name, meta)
            if meta['is_core']:
                self.core_layout.addWidget(ext_widget)
                core_extensions_exist = True
            else:
                self.custom_layout.addWidget(ext_widget)
                custom_extensions_exist = True

        self.core_group.setVisible(core_extensions_exist)
        self.custom_group.setVisible(custom_extensions_exist)

    def _create_extension_widget(self, name, meta):
        frame = QFrame()
        frame.setObjectName("ExtBlock")
        frame.setStyleSheet("""
            #ExtBlock {
                border: 1px solid rgba(128, 128, 128, 0.4);
                border-radius: 6px;
                background-color: rgba(128, 128, 128, 0.05);
                margin-bottom: 5px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)

        title_layout = QHBoxLayout()
        checkbox = QCheckBox(meta.get('display_name', name))
        checkbox.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.checkboxes[name] = checkbox
        title_layout.addWidget(checkbox)
        title_layout.addStretch()
        
        author_label = QLabel(f"<b>{self.lang.get('author_label')}</b> {meta.get('author', 'N/A')}")
        version_label = QLabel(f"<b>{self.lang.get('version_label')}</b> {meta.get('version', 'N/A')}")
        author_label.setStyleSheet("color: #aaa;")
        version_label.setStyleSheet("color: #aaa;")
        title_layout.addWidget(author_label)
        title_layout.addWidget(version_label)
        layout.addLayout(title_layout)

        desc_label = QLabel(meta.get('description', 'No description.'))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("padding-left: 24px; color: #ccc;")
        layout.addWidget(desc_label)

        deps = meta.get('dependencies', [])
        if deps:
            deps_str = ", ".join(d.replace('_', ' ').title() for d in deps)
            deps_label = QLabel(f"<b>{self.lang.get('dependencies_label')}</b> {deps_str}")
            deps_label.setWordWrap(True)
            deps_label.setStyleSheet("padding-left: 24px; font-size: 9pt; color: #888;")
            layout.addWidget(deps_label)

        settings_class = meta.get('settings_gui_class')
        if settings_class:
            settings_widget = settings_class(self.main_window)
            self.settings_widgets[name] = settings_widget
            if hasattr(settings_widget, 'store_initial_state'):
                settings_widget.store_initial_state()

            btn_title = self.lang.get('settings_extensions_settings_tab', 'Extension Settings')
            if btn_title == 'settings_extensions_settings_tab':
                btn_title = 'Extension Settings'

            accordion_btn = QPushButton(f"► {btn_title}")
            accordion_btn.setCheckable(True)
            accordion_btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 5px;
                    font-weight: bold;
                    border: none;
                    background: transparent;
                    color: #29b8db;
                }
                QPushButton:hover {
                    background: rgba(128, 128, 128, 0.1);
                    border-radius: 4px;
                }
            """)
            
            settings_container = QWidget()
            sc_layout = QVBoxLayout(settings_container)
            sc_layout.setContentsMargins(24, 0, 0, 0)
            sc_layout.addWidget(settings_widget)
            settings_container.setVisible(False)

            def toggle_accordion(checked, w=settings_container, b=accordion_btn, t=btn_title):
                w.setVisible(checked)
                b.setText(f"{'▼' if checked else '►'} {t}")

            accordion_btn.toggled.connect(toggle_accordion)

            layout.addWidget(accordion_btn)
            layout.addWidget(settings_container)

        return frame

    def retranslate_ui(self):
        current_states = {name: cb.isChecked() for name, cb in self.checkboxes.items()}

        self.core_group.setTitle(self.lang.get('core_modules_group'))
        self.custom_group.setTitle(self.lang.get('custom_modules_group'))
        
        for i in reversed(range(self.core_layout.count())):
            item = self.core_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
        for i in reversed(range(self.custom_layout.count())):
            item = self.custom_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        self.checkboxes.clear()
        self.settings_widgets.clear()
        self.populate_extensions()

        for name, checkbox in self.checkboxes.items():
            if name in current_states:
                checkbox.setChecked(current_states[name])

    def store_initial_state(self):
        if 'extensions' not in self.extensions_window.state_on_open:
            saved_settings = self.settings_manager.get_setting(['core'], {})
            self.extensions_window.state_on_open['extensions'] = saved_settings.get('extensions', {}).copy()

        ext_settings = self.extensions_window.state_on_open['extensions']
        for name, checkbox in self.checkboxes.items():
            is_enabled = ext_settings.get(f'{name}_enabled', True)
            checkbox.setChecked(is_enabled)
            
        for widget in self.settings_widgets.values():
            if hasattr(widget, 'store_initial_state'):
                widget.store_initial_state()

    def apply_settings(self, is_project=False):
        if 'extensions' not in self.extensions_window.state_on_open:
            self.extensions_window.state_on_open['extensions'] = {}

        for name, checkbox in self.checkboxes.items():
            self.extensions_window.state_on_open['extensions'][f'{name}_enabled'] = checkbox.isChecked()

        for name, widget in self.settings_widgets.items():
            if hasattr(widget, 'get_settings_to_save'):
                ind_settings = widget.get_settings_to_save()
                if ind_settings:
                    self.settings_manager.update_setting(['apps', name, 'settings'], ind_settings, is_project)
            if hasattr(widget, 'apply_settings'):
                widget.apply_settings()

    def revert_settings(self):
        for widget in self.settings_widgets.values():
            if hasattr(widget, 'revert_settings'):
                widget.revert_settings()
        self.store_initial_state()

    def reset_to_defaults(self):
        defaults = self.defaults.get('core', {}).get('extensions', {})
        for name, checkbox in self.checkboxes.items():
            is_enabled = defaults.get(f'{name}_enabled', True)
            checkbox.setChecked(is_enabled)
            
        for widget in self.settings_widgets.values():
            if hasattr(widget, 'reset_to_defaults'):
                widget.reset_to_defaults()