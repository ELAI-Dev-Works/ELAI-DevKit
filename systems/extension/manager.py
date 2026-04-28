import os
from .metadata import MetadataLoader
from .dependency_manager import DependencyManager
from .component_loader import ComponentLoader
from .architectures.v1 import V1Architecture
from .architectures.v2 import V2Architecture
from systems.gui.icons import IconManager

class ExtensionManager:
    def __init__(self, main_window):
        self._main_window = main_window
        self.app_root_path = main_window.app_root_path
        self.core_apps_path = os.path.join(self.app_root_path, "apps")
        self.custom_extensions_path = os.path.join(self.app_root_path, "extensions", "custom_apps")

        self.extensions = {}

        # Connect IconManager
        IconManager.init_paths(self.app_root_path, self)


        # Sub-managers
        self.dep_manager = None # Initialized after discovery
        self.comp_loader = ComponentLoader(main_window)

        # Architectures
        self.architectures = {
            1: V1Architecture(),
            2: V2Architecture()
        }

    @property
    def main_window(self):
        return self._main_window

    @main_window.setter
    def main_window(self, value):
        self._main_window = value
        if hasattr(self, 'comp_loader') and self.comp_loader:
            self.comp_loader.main_window = value

    def discover_extensions(self):
        """Scans folders and builds metadata."""
        self._scan_folder(self.core_apps_path, is_core=True)
        self._scan_folder(self.custom_extensions_path, is_core=False)
        
        # Initialize Dependency Manager with discovered extensions
        self.dep_manager = DependencyManager(self.extensions)
        print(f"[Manager] Discovered extensions: {list(self.extensions.keys())}")

    def _scan_folder(self, base_path, is_core):
        if not os.path.exists(base_path): return
        
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                # Check if it's a valid extension (must have app.py)
                if os.path.exists(os.path.join(item_path, "app.py")):
                    meta = MetadataLoader.load_metadata(item_path, item, is_core)
                    self.extensions[item] = meta

    def load_extensions(self):
        """Loads extension modules respecting dependencies and settings."""
        # 1. Update enabled state from settings
        core_settings = self.main_window.settings_manager.get_setting(['core'], {})
        ext_settings = core_settings.get('extensions', {})
        for name, meta in self.extensions.items():
            meta['enabled'] = ext_settings.get(f'{name}_enabled', True)

        # 2. Resolve Order
        load_order = self.dep_manager.resolve_load_order()
        print(f"[Manager] Extension load order: {load_order}")

        # 3. Load Modules via Architectures
        for name in load_order:
            meta = self.extensions[name]
            if not meta['enabled']: continue

            version = meta.get('structure_version', 1)
            arch = self.architectures.get(version)
            
            if arch:
                if arch.load(meta):
                    # Load UI Components (Settings, QuickSettings) independent of architecture
                    self.comp_loader.load_settings_widgets(meta)
                    print(f"[Manager] Loaded extension: {name} (v{version})")
                else:
                    print(f"[Manager] Failed to load {name}")
                    meta['enabled'] = False
            else:
                print(f"[Manager] Unknown architecture version {version} for {name}")
                meta['enabled'] = False

    def initialize_extensions(self):
        """Instantiates App and GUI classes."""
        for name, meta in self.extensions.items():
            if meta['enabled'] and meta.get('app_module'):
                version = meta.get('structure_version', 1)
                arch = self.architectures.get(version)
                if arch:
                    if not arch.initialize(meta, self.main_window):
                        meta['enabled'] = False

    def connect_ui_extensions(self, key_manager, context_menu_manager):
        """Connects shortcuts and context menus."""
        for name, meta in self.extensions.items():
            if meta['enabled']:
                self.comp_loader.register_ui_hooks(meta, key_manager, context_menu_manager)

    # --- Data Accessors for Main Window ---

    def get_extension_widgets(self):
        """Returns list of (name, widget_class) for main tabs."""
        widgets = []
        for name, meta in self.extensions.items():
            if meta['enabled'] and meta.get('gui_class'):
                widgets.append((name, meta['gui_class']))
        return widgets

    def get_extension_settings_widgets(self):
        """Returns dict of settings classes."""
        settings_widgets = {}
        for name, meta in self.extensions.items():
            if meta['enabled'] and meta.get('settings_gui_class'):
                settings_widgets[name] = meta['settings_gui_class']
        return settings_widgets

    def get_extension_quick_settings_modules(self):
        """Returns dict of quick settings modules."""
        qs_modules = {}
        for name, meta in self.extensions.items():
            if meta['enabled'] and meta.get('quick_settings_gui_module'):
                qs_modules[name] = meta['quick_settings_gui_module']
        return qs_modules

    def reload_extensions(self):
        """Hot-reloads extensions based on current settings."""
        core_settings = self.main_window.settings_manager.get_setting(['core'], {})
        ext_settings = core_settings.get('extensions', {})

        for name, meta in self.extensions.items():
            meta['enabled'] = ext_settings.get(f'{name}_enabled', True)

        load_order = self.dep_manager.resolve_load_order()

        for name in load_order:
            meta = self.extensions[name]

            if meta['enabled'] and not meta.get('instance'):
                version = meta.get('structure_version', 1)
                arch = self.architectures.get(version)
                if arch and arch.load(meta):
                    self.comp_loader.load_settings_widgets(meta)
                    if arch.initialize(meta, self.main_window):
                        print(f"[Manager] Hot-loaded extension: {name}")
                    else:
                        meta['enabled'] = False
                else:
                    meta['enabled'] = False