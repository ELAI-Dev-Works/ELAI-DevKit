import subprocess
import re
from ..error_output_block import generate_error_block

def check_js_ts(temp_file_path: str, content: str) -> str:
    res = subprocess.run(["node", "--check", temp_file_path], capture_output=True, text=True)
    if res.returncode != 0:
        err_msg = res.stderr.strip() or res.stdout.strip()
        match = re.search(r':(\d+)', err_msg)
        line_num = int(match.group(1)) if match else None
        return generate_error_block(content, err_msg, line_num)
    return None