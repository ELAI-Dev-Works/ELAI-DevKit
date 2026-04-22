import os
import sys
import importlib.util
from .base import BaseArchitecture

class V2Architecture(BaseArchitecture):
    """
    Architecture V2:
    - App logic in 'app.py'
    - GUI logic in 'gui/core_window.py'
    - Initialization passes 'context' (AppContext)
    """
    def load(self, meta):
        name = meta['name']
        path = meta['path']
        is_core = meta['is_core']

        try:
            # Load app.py
            app_module_name = f"apps.{name}.app" if is_core else f"extensions.{name}.app"
            app_path = os.path.join(path, "app.py")
            meta["app_module"] = self._import_module(app_module_name, app_path)

            # Load gui/windows/core.py
            gui_module_name = f"apps.{name}.gui.windows.core" if is_core else f"extensions.{name}.gui.windows.core"
            gui_path = os.path.join(path, "gui", "windows", "core.py")
            meta["gui_module"] = self._import_module(gui_module_name, gui_path)
            
            return True
        except Exception as e:
            print(f"[Arch-V2] Error loading {name}: {e}")
            return False

    def initialize(self, meta, main_window):
        # Note: V2 architecture expects 'context', which is accessible via main_window.context
        context = getattr(main_window, 'context', None)
        if not context:
            print(f"[Arch-V2] Error: Context missing for {meta['name']}")
            return False

        name = meta['name']
        camel_name = "".join(part.capitalize() for part in name.split('_'))
        
        try:
            # Init App with Context
            app_class_name = camel_name + "App"
            app_class = getattr(meta["app_module"], app_class_name)
            meta["instance"] = app_class(context)

            # Init GUI Class
            gui_class_name = camel_name + "CoreWindow"
            gui_class = getattr(meta["gui_module"], gui_class_name)
            meta["gui_class"] = gui_class
            
            return True
        except AttributeError as e:
            print(f"[Arch-V2] Init error {name}: {e}")
            return False

    def _import_module(self, name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod