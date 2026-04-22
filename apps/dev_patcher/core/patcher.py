import os
import importlib
import time
from itertools import groupby
from typing import List, Any, Dict, Tuple
from .command_planner import plan_execution_order

# Updated three-tier system for EDIT tools
from .commands.edit.tool import EditTool as StandardEditTool
from .patcher_tools.extra_tool import Tool as ExtraEditTool
from .patcher_tools.experimental.precise_patching import Tool as ExperimentalEditTool
from .custom_loader import CustomCommandLoader

def _normalize_edit_args(args: List[str]) -> List[str]:
    """Helper to normalize EDIT arguments, moving algo flag to end if first."""
    if args and args[0] in ('-v1', '-v2'):
        new_args = list(args)
        flag = new_args.pop(0)
        new_args.append(flag)
        return new_args
    return args

def _get_command_group_key(command: Tuple):
    """
    Returns a key for grouping commands.
    - Consecutive EDIT commands for the same file get the same key.
    - All other commands get a unique key to be processed individually.
    """
    command_name, args, _ = command
    if command_name.upper() == 'EDIT' and args:
        # Determine index of file path based on whether first arg is a version flag
        file_idx = 1
        if args[0] in ('-v1', '-v2'):
            file_idx = 2

        if len(args) > file_idx:
            return f"EDIT_BATCH_{args[file_idx]}"
    return id(command)

def _apply_edit_batch(batch: List[Tuple], fs_handler, experimental_flags):
    """
    Sequentially processes a batch of EDIT commands for a single file.
    """
    if not batch:
        return

    # Extract file path using the same logic as grouping
    first_cmd_args = batch[0][1]
    file_idx = 1
    if first_cmd_args and first_cmd_args[0] in ('-v1', '-v2'):
        file_idx = 2

    # Safety check
    if len(first_cmd_args) <= file_idx:
         # Should not happen if grouped correctly, but fail gracefully
         yield False, "Invalid argument format for EDIT command.", batch[0]
         return

    file_path = first_cmd_args[file_idx]

    try:
        current_content_in_memory = fs_handler.read(file_path)
    except FileNotFoundError:
        for cmd_tuple in batch:
            yield False, f"File not found: {file_path}", cmd_tuple
        return

    final_content = current_content_in_memory

    # --- Select the correct EDIT tool ---
    flags = experimental_flags or {}
    use_lineno = flags.get("lineno")
    use_extra = flags.get("fuzzy") or flags.get("scope")

    edit_tool_instance = None
    if use_lineno:
        edit_tool_instance = ExperimentalEditTool()
        plan_func = lambda args, content, original: edit_tool_instance.plan_edit(args, content, original, flags)
    elif use_extra:
        edit_tool_instance = ExtraEditTool()
        plan_func = lambda args, content, original: edit_tool_instance.plan_edit(args, content, original, flags)
    else: # Basic mode
        edit_tool_instance = StandardEditTool()
        plan_func = lambda args, content, original: edit_tool_instance.plan_edit(args, content, original)

    # Process each command sequentially
    for i, cmd_tuple in enumerate(batch):
        start_time = time.time()
        _, args, content_block = cmd_tuple
    
        # Normalize arguments so that args[0] is the action (expected by Tool)
        norm_args = _normalize_edit_args(args)
    
        plan = plan_func(norm_args, content_block, final_content)
    
        elapsed = time.time() - start_time
        time_str = f" ({elapsed:.3f}s)"
    
        if plan.get('success'):
            lines = final_content.splitlines()
            start, end = plan['start_line'], plan['end_line']
            lines[start:end] = plan['new_lines']
            final_content = '\n'.join(lines)
            msg = plan.get('message', "The edit was successfully applied to memory.")
            yield True, msg + time_str, cmd_tuple
        else:
            msg = plan.get('message', "Unknown planning error.")
            yield False, msg + time_str, cmd_tuple
            for remaining_cmd in batch[i+1:]:
                yield False, "The operation was aborted due to an error in the previous command.", remaining_cmd
            return

    # If everything was successful, write the final result to the file
    fs_handler.write(file_path, final_content)

def run_patch(commands: list, fs_handler, experimental_flags=None):
    """
    Executes a list of patch commands, batching consecutive EDITs on the same file.
    Commands are sorted by a planner before execution.
    """
    if not commands:
        yield True, "No commands to execute.", None
        return

    # Sort commands by execution priority
    # fs_handler.root provides the project path for custom command lookup
    planned_commands = plan_execution_order(commands, fs_handler.root)
    
    # Group consecutive commands based on the key function
    for group_key, group_iter in groupby(planned_commands, key=_get_command_group_key):
        command_group = list(group_iter)

        if "EDIT_BATCH" in str(group_key):
            # This is a batch of EDIT commands for one file
            yield from _apply_edit_batch(command_group, fs_handler, experimental_flags)
        else:
            # Process single (non-EDIT) commands one by one
            for command_tuple in command_group:
                start_time = time.time()
                command_name, args, content = command_tuple
                try:
                    tool_instance = None
                    # 1. Try Standard Command
                    try:
                        module_name = f".commands.{command_name.lower()}"
                        tool_module = importlib.import_module(module_name, package='apps.dev_patcher.core')
                        tool_instance = tool_module.Command()
                    except ImportError:
                        # 2. Try Custom Command
                        loader = CustomCommandLoader(fs_handler.root)
                        tool_module = loader.find_command(command_name)
                        if tool_module and hasattr(tool_module, 'Command'):
                            tool_instance = tool_module.Command()
                        else:
                            raise # Re-raise if not found in custom either
        
                    import inspect
                    sig = inspect.signature(tool_instance.execute)
                    if 'flags' in sig.parameters:
                        success, message = tool_instance.execute(args, content, fs_handler, flags=experimental_flags)
                    else:
                        success, message = tool_instance.execute(args, content, fs_handler)
        
                    elapsed = time.time() - start_time
                    message += f" ({elapsed:.3f}s)"
        
                    yield success, message, command_tuple
                except ImportError:
                    yield False, f"Command '{command_name}' failed: tool not found.", command_tuple
                except Exception as e:
                    yield False, f"Command '{command_name}' failed: unexpected error: {e}", command_tuple