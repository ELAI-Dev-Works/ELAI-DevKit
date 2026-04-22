import sys
import shutil
import subprocess
from tree_sitter_language_pack import get_parser

def check_python_version():
    print("--- 1. Checking Python Version ---")
    print(f"Version: {sys.version.split()[0]}")
    if sys.version_info.major == 3 and sys.version_info.minor >= 8:
        print("  [PASS] Python 3.8+ detected")
    else:
        print("  [WARNING] Python version is older than 3.8. Might cause issues.")

def check_external_tool(name, version_args):
    print(f"--- Checking '{name}' ---")
    if not shutil.which(name):
        print(f"  [WARNING] '{name}' not found in PATH.")
        return False

    try:
        result = subprocess.run(
            version_args,
            capture_output=True,
            text=True,
            shell=True if sys.platform == 'win32' else False
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  [PASS] Found {name}: {version}")
            return True
        else:
            print(f"  [ERROR] '{name}' found but returned error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"  [ERROR] Exception checking '{name}': {e}")
        return False

def check_parser_library():
    print("--- 5. Checking 'tree-sitter-language-pack' library ---")
    try:
        get_parser("python")
        print("  [PASS] Successfully received a working Python parser.")
        return True
    except Exception as e:
        print(f"  [ERROR] A critical error occurred: {e}")
        print("          Try deleting the '.venv' folder and running RUN.BAT again.")
        return False

if __name__ == "__main__":
    print("Running Environment Diagnostics...\n")
    check_python_version()
    check_external_tool("uv", ["uv", "--version"])
    check_external_tool("node", ["node", "-v"])
    check_external_tool("npm", ["npm", "-v"])
    if not check_parser_library():
        sys.exit(1)