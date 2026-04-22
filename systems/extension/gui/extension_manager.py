import tomllib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QCheckBox,
    QSpacerItem, QSizePolicy, QFormLayout, QScrollArea
)
from systems.settings.defaults import main_default_settings

class ExtensionManagerWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.lang = main_window.lang
        self.extension_manager = main_window.extension_manager
        self.settings_manager = main_window.settings_manager
        self.checkboxes = {}
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
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 10)

        title_layout = QHBoxLayout()
        checkbox = QCheckBox(meta.get('display_name', name))
        checkbox.setStyleSheet("font-weight: bold;")
        self.checkboxes[name] = checkbox
        title_layout.addWidget(checkbox)
        title_layout.addStretch()
        author_label = QLabel(f"{self.lang.get('author_label')} {meta.get('author', 'N/A')}")
        version_label = QLabel(f"{self.lang.get('version_label')} {meta.get('version', 'N/A')}")
        author_label.setStyleSheet("font-size: 9pt; color: #aaa;")
        version_label.setStyleSheet("font-size: 9pt; color: #aaa;")
        title_layout.addWidget(author_label)
        title_layout.addWidget(version_label)
        layout.addLayout(title_layout)

        desc_label = QLabel(meta.get('description', 'No description.'))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("padding-left: 20px;")
        layout.addWidget(desc_label)

        deps = meta.get('dependencies', [])
        if deps:
            deps_str = ", ".join(d.replace('_', ' ').title() for d in deps)
            deps_label = QLabel(f"<b>{self.lang.get('dependencies_label')}</b> {deps_str}")
            deps_label.setWordWrap(True)
            deps_label.setStyleSheet("padding-left: 20px; font-size: 9pt;")
            layout.addWidget(deps_label)

        return widget

    def retranslate_ui(self):
        # Save current checkbox states before recreating widgets
        current_states = {}
        for name, checkbox in self.checkboxes.items():
            current_states[name] = checkbox.isChecked()
        
        self.core_group.setTitle(self.lang.get('core_modules_group'))
        self.custom_group.setTitle(self.lang.get('custom_modules_group'))
        for i in reversed(range(self.core_layout.count())):
            item = self.core_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
        for i in reversed(range(self.custom_layout.count())):
            item = self.custom_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
        self.populate_extensions()
        
        # Restore saved states instead of loading from file
        for name, checkbox in self.checkboxes.items():
            if name in current_states:
                checkbox.setChecked(current_states[name])

    def store_initial_state(self):
        # Check if parent panel has state_on_open with extensions
        parent_panel = self.parent()
        while parent_panel and not hasattr(parent_panel, 'state_on_open'):
            parent_panel = parent_panel.parent()
        
        # If parent has extensions state, use it (preserves applied but unsaved changes)
        if parent_panel and hasattr(parent_panel, 'state_on_open') and 'extensions' in parent_panel.state_on_open:
            ext_settings = parent_panel.state_on_open['extensions']
        else:
            # Otherwise load from file (first time opening settings)
            settings = self.settings_manager.get_setting(['core'], self.defaults)
            ext_settings = settings.get('extensions', {})
        
        for name, checkbox in self.checkboxes.items():
            is_enabled = ext_settings.get(f'{name}_enabled', True)
            checkbox.setChecked(is_enabled)

    def apply_settings(self):
        # Update the parent's state_on_open with current checkbox states
        parent_panel = self.parent()
        while parent_panel and not hasattr(parent_panel, 'state_on_open'):
            parent_panel = parent_panel.parent()
        
        if parent_panel and hasattr(parent_panel, 'state_on_open'):
            if 'extensions' not in parent_panel.state_on_open:
                parent_panel.state_on_open['extensions'] = {}
            
            for name, checkbox in self.checkboxes.items():
                parent_panel.state_on_open['extensions'][f'{name}_enabled'] = checkbox.isChecked()

    def get_settings_to_save(self):
        settings_to_save = {}
        for name, checkbox in self.checkboxes.items():
            settings_to_save[f'{name}_enabled'] = checkbox.isChecked()
        return {'extensions': settings_to_save}

    def revert_settings(self):
        self.store_initial_state()

    def reset_to_defaults(self):
        defaults = self.defaults.get('core', {}).get('extensions', {})
        for name, checkbox in self.checkboxes.items():
            is_enabled = defaults.get(f'{name}_enabled', True)
            checkbox.setChecked(is_enabled)