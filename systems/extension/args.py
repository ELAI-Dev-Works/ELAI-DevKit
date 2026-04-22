import argparse
import sys
import os
import importlib.util

class ArgsManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.parser = argparse.ArgumentParser(description="PatcherApp Launcher")
        self.extension_handlers = {}
        self._discover_arg_handlers()

    def _discover_arg_handlers(self):
        for name, meta in self.main_window.extension_manager.extensions.items():
            if not meta.get("enabled"):
                continue

            arg_file_path = os.path.join(meta["path"], "args.py")
            if os.path.exists(arg_file_path):
                try:
                    arg_module_name = f"apps.{name}.args" if meta["is_core"] else f"extensions.{name}.args"
                    spec = importlib.util.spec_from_file_location(arg_module_name, arg_file_path)
                    arg_module = importlib.util.module_from_spec(spec)
                    sys.modules[arg_module_name] = arg_module
                    spec.loader.exec_module(arg_module)

                    if hasattr(arg_module, 'register_args') and hasattr(arg_module, 'handle_args'):
                        arg_module.register_args(self.parser)
                        self.extension_handlers[name] = arg_module.handle_args
                        print(f"Discovered command-line arguments for extension: {name}")
                except Exception as e:
                    print(f"Error discovering args for extension {name}: {e}")

    def parse_and_handle(self):
        """
        Parses command-line arguments and calls extension handlers.
    
        Returns:
            tuple: (handled: bool, should_exit: bool)
            - handled: True if any argument was processed
            - should_exit: True if the app should quit after handling
        """
        if len(sys.argv) > 1:
            args = self.parser.parse_args()
            any_handled = False
            should_exit = False
    
            for handler in self.extension_handlers.values():
                result = handler(args, self.main_window)
    
                # Support new tuple format (handled, should_exit) and legacy bool
                if isinstance(result, tuple):
                    handled, exit_flag = result
                else:
                    # Legacy: True means handled; for backward compatibility, 
                    # we don't exit unless explicitly requested
                    handled = bool(result)
                    exit_flag = False
    
                if handled:
                    any_handled = True
                if exit_flag:
                    should_exit = True
    
            return (any_handled, should_exit)
        return (False, False)