import os
import pkgutil
import importlib
import sys
from typing import Tuple, List

def run(args, content, fs_handler):
    """
    Scans and lists all available commands and their arguments (Standard + Custom).
    Usage:
        TEST -command_list -all
        TEST -command_list -command <edit|manage>
        TEST -command_list -doc
    """
    output = []
    output.append("=== DevPatcher Command Registry ===")

    show_all = '-all' in args
    show_doc = '-doc' in args
    target_commands = []

    if '-command' in args:
        try:
            idx = args.index('-command')
            # Extract commands list <cmd1|cmd2>
            val = args[idx+1]
            if val.startswith('<') and val.endswith('>'):
                target_commands = [c.strip().upper() for c in val[1:-1].split('|')]
        except (IndexError, ValueError):
            return False, "Invalid syntax for -command. Use <cmd1|cmd2>."

    if not show_all and not target_commands:
         output.append("[INFO] showing default summary. Use -all for full list or -command <name> for specific.")

    commands_map = {}

    # --- 1. Standard Commands Inspection ---
    core_commands = ['manage', 'project', 'git', 'download', 'edit', 'test']

    # Pre-populate special commands that don't follow the 'execute' folder pattern
    commands_map['EDIT'] = {'-replace', '-insert', '-remove'}
    commands_map['GIT'] = {'(See documentation for git commands like clone, pull, etc.)'}
    commands_map['DOWNLOAD'] = {'(See documentation for URL and destination args)'}

    for cmd in core_commands:
        cmd_upper = cmd.upper()

        # Filtering
        if target_commands and cmd_upper not in target_commands:
            continue

        if cmd_upper not in commands_map:
            commands_map[cmd_upper] = set()

        # Special Skip for manually populated
        if cmd_upper in ['EDIT', 'GIT', 'DOWNLOAD'] and not show_all and not target_commands:
             continue

        try:
            exec_mod_name = f"apps.dev_patcher.core.commands.{cmd}.execute"
            exec_mod = importlib.import_module(exec_mod_name)

            if hasattr(exec_mod, '__path__'):
                for _, arg_name, _ in pkgutil.iter_modules(exec_mod.__path__):
                    # Filter out internal helper modules
                    if not arg_name.startswith('_') and arg_name not in ['base', 'utils']:
                        commands_map[cmd_upper].add(f"-{arg_name}")

                        # Special case for PROJECT -setup to find its sub-arguments
                        if cmd_upper == 'PROJECT' and arg_name == 'setup':
                            try:
                                setup_args_mod_name = f"{exec_mod_name}.setup_args"
                                setup_args_mod = importlib.import_module(setup_args_mod_name)
                                if hasattr(setup_args_mod, '__path__'):
                                    for _, sub_arg_name, _ in pkgutil.iter_modules(setup_args_mod.__path__):
                                        if not sub_arg_name.startswith('_'):
                                            commands_map[cmd_upper].add(f"  └─ (for -setup) -{sub_arg_name}")
                            except ImportError:
                                pass # No setup_args module found
        except (ImportError, ModuleNotFoundError):
            pass
        except Exception as e:
            output.append(f"[Warning] Failed to scan standard command {cmd}: {e}")

    # --- 2. Custom Commands Inspection ---
    custom_root = os.path.join(fs_handler.root, 'extensions', 'custom_commands')
    
    if os.path.isdir(custom_root):
        for ext_name in os.listdir(custom_root):
            ext_path = os.path.join(custom_root, ext_name)
            if not os.path.isdir(ext_path): continue

            cmds_path = os.path.join(ext_path, 'commands')
            if os.path.isdir(cmds_path):
                for cmd_name in os.listdir(cmds_path):
                    cmd_upper = cmd_name.upper()

                    if target_commands and cmd_upper not in target_commands:
                         continue

                    if cmd_upper not in commands_map:
                        commands_map[cmd_upper] = set()

                    exec_path = os.path.join(cmds_path, cmd_name, 'execute')
                    if os.path.isdir(exec_path):
                        for item in os.listdir(exec_path):
                            if item.endswith('.py') and not item.startswith('__'):
                                arg_name = item[:-3]
                                commands_map[cmd_upper].add(f"-{arg_name} (Custom)")
                            elif os.path.isdir(os.path.join(exec_path, item)) and os.path.exists(os.path.join(exec_path, item, '__init__.py')):
                                commands_map[cmd_upper].add(f"-{item} (Custom)")

    # --- 3. Format Output ---
    for cmd in sorted(commands_map.keys()):
        output.append(f"[{cmd}]")
        args_list = sorted(list(commands_map[cmd]))
        if args_list:
            for arg in args_list:
                output.append(f"  {arg}")
        else:
            output.append("  (No explicit arguments found)")

        if show_doc:
             output.append("  [Documentation placeholder: Would load .cdoc here]")

        output.append("")

    return True, "\n".join(output)

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res = []
    succ, msg = run(['-command_list', '-all'], '', vfs)
    passed = succ and "[EDIT]" in msg
    res.append(("Command List All", passed, msg))
    return res
