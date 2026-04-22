import subprocess
import sys
from typing import Tuple

def execute_script(script_path: str, root_path: str) -> Tuple[bool, str, str]:
    """
    Executes a standalone Python script in isolation.
    """
    try:
        result = subprocess.run([sys.executable, script_path],
            cwd=root_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Execution timed out."
    except Exception as e:
        return False, "", str(e)

def execute_test(test_path: str, root_path: str) -> Tuple[bool, str, str]:
    """
    Executes a Python unit test file.
    """
    try:
        result = subprocess.run([sys.executable, "-m", "unittest", "-v", test_path],
            cwd=root_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Execution timed out."
    except Exception as e:
        return False, "", str(e)