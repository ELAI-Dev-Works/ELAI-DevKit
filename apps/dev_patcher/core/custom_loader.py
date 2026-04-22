import os
import importlib.util
import sys

class CustomCommandLoader:
    """
    Handles discovery and loading of custom commands from the project's 'custom_commands' directory.
    """
    def __init__(self, project_root):
        self.project_root = project_root
        self.custom_dir = os.path.join(self.project_root, 'extensions', 'custom_commands') if self.project_root else None
    
    def _get_module_from_path(self, file_path, module_name):
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
        except Exception as e:
            print(f"Failed to load custom module {file_path}: {e}")
        return None

    def find_command(self, command_name):
        """
        Looks for a top-level command module: custom_commands/*/commands/<command_name>/__init__.py
        """
        if not self.custom_dir or not os.path.isdir(self.custom_dir):
            return None

        # Scan all extension folders in custom_commands
        for ext_name in os.listdir(self.custom_dir):
            cmd_path = os.path.join(self.custom_dir, ext_name, 'commands', command_name.lower(), '__init__.py')
            if os.path.exists(cmd_path):
                return self._get_module_from_path(cmd_path, f"custom_cmd_{command_name}")
        return None

    def find_action(self, command_name, action_name):
        """
        Looks for a sub-action module: custom_commands/*/commands/<command_name>/execute/<action_name>.py
        """
        if not self.custom_dir or not os.path.isdir(self.custom_dir):
            return None

        for ext_name in os.listdir(self.custom_dir):
            action_path = os.path.join(self.custom_dir, ext_name, 'commands', command_name.lower(), 'execute', f"{action_name}.py")
            # Also support folders for actions (like project -> setup) if they have __init__.py? 
            # For now, following the pattern file.py or folder/__init__.py
            if os.path.exists(action_path):
                return self._get_module_from_path(action_path, f"custom_act_{command_name}_{action_name}")
            
            # Check for folder based action
            action_folder_init = os.path.join(self.custom_dir, ext_name, 'commands', command_name.lower(), 'execute', action_name, '__init__.py')
            if os.path.exists(action_folder_init):
                 return self._get_module_from_path(action_folder_init, f"custom_act_{command_name}_{action_name}")

        return None