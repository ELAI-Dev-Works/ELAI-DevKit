import importlib
from typing import List, Tuple
from .custom_loader import CustomCommandLoader

DEFAULT_PRIORITY = 99

def get_command_priority(command_tuple: Tuple, project_root: str, custom_loader=None) -> int:
    """
    Determines the priority of a command by inspecting its class.
    """
    command_name = command_tuple[0]
    args = command_tuple[1]

    # 1. Try Standard Command
    try:
        # Assuming the standard commands are located in the same package structure
        module_name = f"apps.dev_patcher.core.commands.{command_name.lower()}"
        module = importlib.import_module(module_name)
        if hasattr(module, 'Command'):
            return module.Command().get_priority(args)
    except (ImportError, AttributeError):
        pass

    # 2. Try Custom Command
    if not custom_loader and project_root:
        custom_loader = CustomCommandLoader(project_root)

    if custom_loader:
        module = custom_loader.find_command(command_name)
        if module and hasattr(module, 'Command'):
            try:
                return module.Command().get_priority(args)
            except Exception:
                pass

    return DEFAULT_PRIORITY

def plan_execution_order(commands: List[Tuple], project_root: str = None) -> List[Tuple]:
    """
    Sorts a list of commands based on their execution priority.
    The sort is stable.
    """
    if not commands:
        return []

    # Create loader once for the batch if project_root is available
    loader = CustomCommandLoader(project_root) if project_root else None

    def sort_key(cmd):
        return get_command_priority(cmd, project_root, loader)

    sorted_commands = sorted(commands, key=sort_key)
    return sorted_commands