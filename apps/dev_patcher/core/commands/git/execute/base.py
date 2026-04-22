import os
import subprocess
from typing import Tuple
from typing import List

def run(args: list, content: str, fs_handler) -> Tuple[bool, str]:
    """
    Executes Git commands.
    """
    # PROTECTION: If we are in VirtualFileSystem, we do NOT have to execute real Git commands.
    # Because they write on the disk and they can freeze.
    if fs_handler.__class__.__name__ == 'VirtualFileSystem':
        if not args:
             return False, "GIT command requires arguments."
        return True, f"[SIMULATION] Git command syntax OK. Execution of 'git {' '.join(args)}' skipped."
    
    if not args:
        return False, "The GIT command requires arguments (e.g. clone, init, pull)."

    command = ["git"] + args
    working_dir = fs_handler.root

    git_env = os.environ.copy()
    git_env['GIT_TERMINAL_PROMPT'] = '0'

    try:
        if not os.path.isdir(working_dir):
            if args[0] == 'clone':
                os.makedirs(working_dir, exist_ok=True)
            else:
                return False, f"The working directory for Git does not exist: {working_dir}"

        process = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            errors='ignore',
            env=git_env,
            timeout=300
        )

        output = process.stdout.strip()
        if process.stderr:
            output += f"\nSTDERR:\n{process.stderr.strip()}"

        return True, f"Command 'git {' '.join(args)}' completed successfully.\n{output}"

    except FileNotFoundError:
        return False, "Command 'git' not found. Make sure Git is installed and available in your system PATH."
    except subprocess.TimeoutExpired:
        return False, f"The command 'git {' '.join(args)}' took too long to run and was terminated."
    except subprocess.CalledProcessError as e:
        error_message = f"Error executing 'git {' '.join(args)}' (return code {e.returncode})."
        if e.stdout:
            error_message += f"\nSTDOUT:\n{e.stdout.strip()}"
        if e.stderr:
            error_message += f"\nSTDERR:\n{e.stderr.strip()}"
        return False, error_message
    except Exception as e:
        return False, f"An unexpected error occurred while executing GIT command: {e}"

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res = []
    succ, msg = run(['init'], '', vfs)
    passed = succ and "[SIMULATION]" in msg
    res.append(("Git Simulation Mode", passed, msg))
    return res
