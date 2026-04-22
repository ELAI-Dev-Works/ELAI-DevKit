import os
import sys
import importlib.util
from .base import BaseArchitecture

class V1Architecture(BaseArchitecture):
    """
    Architecture V1:
    - App logic in 'app.py'
    - GUI logic in 'app_gui.py'
    - Initialization passes 'main_window' directly
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

            # Load app_gui.py
            gui_module_name = f"apps.{name}.app_gui" if is_core else f"extensions.{name}.app_gui"
            gui_path = os.path.join(path, "app_gui.py")
            meta["gui_module"] = self._import_module(gui_module_name, gui_path)
            
            return True
        except Exception as e:
            print(f"[Arch-V1] Error loading {name}: {e}")
            return False

    def initialize(self, meta, main_window):
        name = meta['name']
        camel_name = "".join(part.capitalize() for part in name.split('_'))
        
        try:
            # Init App
            app_class_name = camel_name + "App"
            app_class = getattr(meta["app_module"], app_class_name)
            meta["instance"] = app_class(main_window)

            # Init GUI Class (Not instance yet, instantiated by MainWindow tab creation)
            gui_class_name = camel_name + "Widget"
            gui_class = getattr(meta["gui_module"], gui_class_name)
            meta["gui_class"] = gui_class
            
            return True
        except AttributeError as e:
            print(f"[Arch-V1] Init error {name}: {e}")
            return False

    def _import_module(self, name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod