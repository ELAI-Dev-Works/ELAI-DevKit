import subprocess
import re
from ..error_output_block import generate_error_block

def check_python(temp_file_path: str, content: str, python_exe: str) -> str:
    res = subprocess.run([python_exe, "-m", "py_compile", temp_file_path], capture_output=True, text=True)
    if res.returncode != 0:
        err_msg = res.stderr.strip() or res.stdout.strip()
        match = re.search(r'line (\d+)', err_msg)
        line_num = int(match.group(1)) if match else None
        return generate_error_block(content, err_msg, line_num)
    return None