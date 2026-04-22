import os
import importlib.util
import sys

class ComponentLoader:
    """
    Handles loading of UI components (Settings, QuickSettings, Shortcuts, Context Menus).
    """
    def __init__(self, main_window):
        self.main_window = main_window

    def load_settings_widgets(self, meta):
        """Loads settings/main.py and settings/quick.py."""
        name = meta['name']
        path = meta['path']
        is_core = meta['is_core']

        # 1. Main Settings Widget
        settings_path = os.path.join(path, "gui", "settings", "main.py")
        if os.path.exists(settings_path):
            try:
                mod_name = f"apps.{name}.gui.settings.main" if is_core else f"extensions.{name}.gui.settings.main"
                mod = self._import_module_from_path(mod_name, settings_path)
                
                class_name = "".join(part.capitalize() for part in name.split('_')) + "SettingsWidget"
                if hasattr(mod, class_name):
                    meta["settings_gui_class"] = getattr(mod, class_name)
            except Exception as e:
                print(f"[ComponentLoader] Error loading settings for {name}: {e}")

        # 2. Quick Settings Widget
        quick_settings_path = os.path.join(path, "gui", "settings", "quick.py")
        if os.path.exists(quick_settings_path):
            try:
                mod_name = f"apps.{name}.gui.settings.quick" if is_core else f"extensions.{name}.gui.settings.quick"
                mod = self._import_module_from_path(mod_name, quick_settings_path)
                
                # We store the module because QuickSettingsPanel uses get_quick_settings() function, 
                # not just a class instantiation
                meta["quick_settings_gui_module"] = mod
            except Exception as e:
                print(f"[ComponentLoader] Error loading quick settings for {name}: {e}")

    def register_ui_hooks(self, meta, key_manager, context_menu_manager):
        """Registers shortcuts and context menus."""
        name = meta['name']
        path = meta['path']
        is_core = meta['is_core']
        
        gui_instance = self.main_window.tabs.get(name)
        if not gui_instance:
            return

        # Shortcuts
        shortcuts_path = os.path.join(path, "gui", "utils", "shortcuts.py")
        if os.path.exists(shortcuts_path):
            try:
                mod_name = f"apps.{name}.gui.utils.shortcuts" if is_core else f"extensions.{name}.gui.utils.shortcuts"
                mod = self._import_module_from_path(mod_name, shortcuts_path)
                if hasattr(mod, 'setup'):
                    mod.setup(key_manager, gui_instance)
            except Exception as e:
                print(f"[ComponentLoader] Error loading shortcuts for {name}: {e}")

        # Context Menus
        cm_path = os.path.join(path, "gui", "utils", "ctx_menu.py")
        if os.path.exists(cm_path):
            try:
                mod_name = f"apps.{name}.gui.utils.ctx_menu" if is_core else f"extensions.{name}.gui.utils.ctx_menu"
                mod = self._import_module_from_path(mod_name, cm_path)
                if hasattr(mod, 'setup'):
                    mod.setup(context_menu_manager, gui_instance)
            except Exception as e:
                print(f"[ComponentLoader] Error loading context menus for {name}: {e}")

    def _import_module_from_path(self, module_name, file_path):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod