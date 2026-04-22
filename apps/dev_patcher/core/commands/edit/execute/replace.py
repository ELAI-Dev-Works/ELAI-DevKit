import os
from typing import Tuple
from ..tool import EditTool

def run(args: list, content: str, fs_handler) -> Tuple[bool, str]:
    if len(args) < 2:
        return False, "EDIT -replace requires a file path."

    file_path = args[1]
    
    try:
        if not fs_handler.exists(file_path):
            return False, f"File not found: {fs_handler._to_abs(file_path)}"
        
        original_content = fs_handler.read(file_path)
    except FileNotFoundError:
        return False, f"File not found: {file_path}"
    except Exception as e:
        return False, f"Error reading file {file_path}: {e}"

    edit_tool_instance = EditTool()
    plan = edit_tool_instance.plan_edit(args, content, original_content)

    if not plan.get("success"):
        return False, plan.get("message", "Failed to plan edit.")

    lines = original_content.splitlines()
    start, end = plan['start_line'], plan['end_line']
    lines[start:end] = plan['new_lines']

    try:
        fs_handler.write(file_path, '\n'.join(lines))
    except Exception as e:
        return False, f"Error writing to file {file_path}: {e}"
        
    return True, plan.get("message", f"File '{os.path.basename(file_path)}' updated.")

from typing import List

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    vfs.write('@ROOT/test_rep.py', 'a = 1\nb = 2\nc = 3')
    content = "---old---\nb = 2\n---new---\nb = 99"
    succ, msg = run(['-replace', '@ROOT/test_rep.py', '-v2'], content, vfs)
    passed = succ and 'b = 99' in vfs.read('@ROOT/test_rep.py')
    res.append(("Replace Content", passed, msg))
    return res
