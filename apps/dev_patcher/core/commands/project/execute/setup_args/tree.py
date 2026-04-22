import os
from typing import Tuple

def parse(args_list: list) -> bool:
    if '-tree' in args_list:
        args_list.remove('-tree')
        return True
    return False

def run(fs, structure_content: str) -> Tuple[bool, str]:
    lines = structure_content.strip().splitlines()
    if not lines: return True, "The tree structure is empty."
    if lines[0].strip().endswith('/'): lines = lines[1:]
    
    path_stack, level_stack = ["@ROOT"], [-1]
    for line in lines:
        line = line.rstrip()
        if not line.strip() or line.strip() in ['│', '|']: continue
        
        level = 0
        temp_line = line
        while temp_line.startswith(('│   ', '    ')):
            level += 1
            temp_line = temp_line[4:]
            
        name = ""
        for prefix in ["├── ", "└── "]:
            if temp_line.startswith(prefix):
                name = temp_line[len(prefix):].strip()
                break
        if not name: continue
        
        while level <= level_stack[-1]:
            path_stack.pop()
            level_stack.pop()
            
        parent_path = path_stack[-1]
        is_dir = name.endswith('/')
        clean_name = name.rstrip('/')
        current_path = os.path.join(parent_path, clean_name).replace('\\', '/')
        
        try:
            if is_dir:
                fs.makedirs(current_path)
            else:
                parent_dir = os.path.dirname(current_path)
                if parent_dir and not fs.exists(parent_dir):
                     fs.makedirs(parent_dir)
                # Create file only if it doesn't exist to avoid overwriting
                if not fs.exists(current_path):
                    fs.write(current_path, "")
        except Exception as e:
            return False, f"Failed to create '{current_path}': {e}"
            
        if is_dir:
            path_stack.append(current_path)
            level_stack.append(level)
            
    return True, "The tree file structure has been created."

from typing import List, Tuple

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    parsed = parse(['-tree', 'something'])
    res.append(("Parse Tree", parsed is True, str(parsed)))

    content = "@ROOT/\n├── src/\n│   └── main.py\n└── data/"
    succ, msg = run(vfs, content)
    passed = succ and vfs.is_dir('@ROOT/src') and vfs.exists('@ROOT/src/main.py') and vfs.is_dir('@ROOT/data')
    res.append(("Tree Generation", passed, msg))
    return res
