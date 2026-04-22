import sys
import os
import subprocess
import shutil

IS_WINDOWS = sys.platform == 'win32'

def get_venv_python_path(root_path):
    """Returns the path to the python executable within the venv."""
    if IS_WINDOWS:
        return os.path.join(root_path, '.venv', 'Scripts', 'python.exe')
    return os.path.join(root_path, '.venv', 'bin', 'python')

def get_venv_bin_dir(root_path):
    """Returns the bin/Scripts directory of the venv."""
    if IS_WINDOWS:
        return os.path.join(root_path, '.venv', 'Scripts')
    return os.path.join(root_path, '.venv', 'bin')

def open_file_externally(path):
    """Opens a file or directory using the default OS application."""
    try:
        if IS_WINDOWS:
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.call(['open', path])
        else:
            subprocess.call(['xdg-open', path])
    except Exception as e:
        print(f"Error opening file externally: {e}")

def get_shell():
    """Returns the default shell command."""
    if IS_WINDOWS:
        return "powershell.exe"
    # Prefer zsh on mac/linux if available, else bash
    if shutil.which("zsh"):
        return shutil.which("zsh")
    return shutil.which("bash") or "/bin/sh"

def is_windows():
    return IS_WINDOWS

def get_creation_flags_detached():
    """Returns flags to spawn a detached process."""
    if IS_WINDOWS:
        return subprocess.CREATE_NEW_CONSOLE
    return 0 # On POSIX, use start_new_session=True in Popen call instead