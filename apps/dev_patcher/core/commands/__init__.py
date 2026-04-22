import importlib
from typing import Tuple, Optional, Any
from ..custom_loader import CustomCommandLoader

class BaseCommand:
    """
    Base class for all patcher commands.
    Ensures that every command has a consistent interface.
    """
    
    PRIORITY = 99
    
    def get_priority(self, args: list) -> int:
        """
        Returns the execution priority of the command.
        Lower numbers execute first.
        """
        return self.PRIORITY
    
    def _load_action_module(self, command_name: str, action_name: str, package: str, project_root: str) -> Optional[Any]:
        """
        Attempts to load an action module, falling back to custom commands.
        """
        # 1. Try to load the standard, built-in action module
        try:
            module = importlib.import_module(f".execute.{action_name}", package)
            return module
        except ImportError:
            pass  # If not found, fall through to the custom loader

        # 2. If standard module fails, try to find a custom action module
        if project_root:
            loader = CustomCommandLoader(project_root)
            custom_module = loader.find_action(command_name.lower(), action_name)
            if custom_module:
                return custom_module

        # 3. If not found in either location
        return None

    def build_backup(self, args: list, content: str, project_root: str, backup_builder) -> None:
        """
        Determines backup actions for this command.
        """
        pass

    def execute(self, args: list, content: str, fs_handler) -> Tuple[bool, str]:
        """
        Executes the command. This method must be implemented by all subclasses.

        :param args: A list of arguments for the command.
        :param content: The content block of the command.
        :param fs_handler: An instance of a file system handler (real or virtual).
        :return: A tuple containing a success boolean and a message.
        """
        raise NotImplementedError("Each command must implement the execute method.")