import sys
import os

def get_current_os():
    if sys.platform == 'win32':
        return 'windows'
    elif sys.platform == 'darwin':
        return 'mac'
    return 'linux'

def get_executable_ext(target_os):
    return '.exe' if target_os == 'windows' else ''