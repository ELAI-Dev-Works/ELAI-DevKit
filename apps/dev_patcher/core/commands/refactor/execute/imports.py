import os
import re
from typing import Tuple
from apps.dev_patcher.core.parser import PARSER

def run(args: list, content: str, fs) -> Tuple[bool, str]:
    if not PARSER:
        return False, "Tree-sitter parser is not initialized."

    # Parse Arguments
    def get_arg_val(key):
        try:
            val = args[args.index(key) + 1]
            if val.startswith('<') and val.endswith('>'):
                return val[1:-1]
            return val
        except (ValueError, IndexError):
            return None

    # Operations
    update_old = get_arg_val("-update") # old
    update_new = None
    if "-update" in args:
        try:
            to_idx = args.index("to")
            raw_new = args[to_idx+1]
            if raw_new.startswith('<') and raw_new.endswith('>'):
                update_new = raw_new[1:-1]
        except: pass

    add_mod = get_arg_val("-add")
    add_scope = None
    if "-add" in args:
         try:
            to_idx = args.index("to", args.index("-add")) # Find 'to' after '-add'
            raw_scope = args[to_idx+1]
            if raw_scope.startswith('<') and raw_scope.endswith('>'):
                add_scope = raw_scope[1:-1]
         except: pass

    remove_mod = get_arg_val("-remove")

    # Files to process
    # If -add scope is provided (e.g. @ROOT/src), find files there. 
    # Otherwise use standard project scan.
    target_path = add_scope if add_scope else fs.root
    
    # Files collection
    files_to_scan = []
    
    # Resolving path for scanning
    abs_target = fs._to_abs(target_path)
    
    # If explicit files block exists, use it (overrides scope)
    if "---files---" in content:
        files_block = content.split("---files---")[1].split("---")[0].strip()
        files_to_scan = [f.strip() for f in files_block.splitlines() if f.strip()]
    else:
        # Scan directory
        if fs.exists(target_path) and not fs.is_dir(target_path):
            files_to_scan.append(target_path)
        else:
            for root, dirs, files in fs.walk(target_path):
                if ".git" in dirs: dirs.remove(".git")
                if "__pycache__" in dirs: dirs.remove("__pycache__")
                for file in files:
                    if file.endswith(".py"):
                        files_to_scan.append(os.path.join(root, file))

    modified_count = 0
    
    for file_path in files_to_scan:
        try:
            rel_path = os.path.relpath(file_path, fs.root).replace('\\', '/') if os.path.isabs(file_path) else file_path
            code = fs.read(rel_path)
            code_bytes = code.encode('utf8')
            tree = PARSER.parse(code_bytes)
            
            modified = False
            new_code = code

            # --- Logic: Update ---
            if update_old and update_new:
                # Find dotted_name nodes matching update_old
                # We do text replacement for simplicity on matches, avoiding partial matches manually
                pattern = re.compile(rf'(^|\s)import\s+{re.escape(update_old)}(\s|$)|(^|\s)from\s+{re.escape(update_old)}(\s|$)')
                
                # Simple regex replace is risky, let's look at lines containing imports
                lines = new_code.splitlines()
                for i, line in enumerate(lines):
                    if line.strip().startswith("import ") or line.strip().startswith("from "):
                        # Replace whole word
                        # "from utils import" -> "from core.utils import"
                        # "import utils" -> "import core.utils"
                        
                        # Regex replacement for strict word boundary
                        line = re.sub(rf'\b{re.escape(update_old)}\b', update_new, line)
                        if line != lines[i]:
                            lines[i] = line
                            modified = True
                new_code = "\n".join(lines)

            # --- Logic: Remove ---
            if remove_mod:
                lines = new_code.splitlines()
                filtered_lines = []
                for line in lines:
                    stripped = line.strip()
                    # Check if line is exactly "import mod" or "from mod import ..."
                    # Handle "import x, mod, y" is harder. Assuming simple imports per line for now.
                    if stripped == f"import {remove_mod}" or stripped.startswith(f"from {remove_mod} import"):
                        modified = True
                        continue # Skip (delete)
                    filtered_lines.append(line)
                new_code = "\n".join(filtered_lines)

            # --- Logic: Add ---
            if add_mod:
                # Check if already present
                if f"import {add_mod}" not in new_code and f"from {add_mod}" not in new_code:
                    lines = new_code.splitlines()
                    last_import_idx = -1
                    
                    # Find last import
                    for i, line in enumerate(lines):
                        if line.startswith("import ") or line.startswith("from "):
                            last_import_idx = i
                    
                    import_stmt = f"import {add_mod}"
                    if last_import_idx != -1:
                        lines.insert(last_import_idx + 1, import_stmt)
                    else:
                        # Insert at top (after potential shebang/encoding)
                        insert_pos = 0
                        if lines and lines[0].startswith("#"):
                             insert_pos = 1
                        lines.insert(insert_pos, import_stmt)
                    
                    new_code = "\n".join(lines)
                    modified = True

            if modified:
                fs.write(rel_path, new_code)
                modified_count += 1

        except Exception as e:
            print(f"Error processing imports in {file_path}: {e}")

    return True, f"Imports refactored in {modified_count} files."

from typing import List

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    vfs.write('@ROOT/test_import.py', 'import os\nimport pdb\n')
    succ, msg = run(['-imports', '-add', '<sys>', 'to', '<@ROOT/test_import.py>'], '', vfs)
    passed = succ and 'import sys' in vfs.read('@ROOT/test_import.py')
    res.append(("Add Import", passed, msg))

    succ, msg = run(['-imports', '-update', '<os>', 'to', '<os.path>'], '---files---\n@ROOT/test_import.py\n---', vfs)
    passed = succ and 'import os.path' in vfs.read('@ROOT/test_import.py') and 'import os\n' not in vfs.read('@ROOT/test_import.py')
    res.append(("Update Import", passed, msg))

    succ, msg = run(['-imports', '-remove', '<pdb>'], '---files---\n@ROOT/test_import.py\n---', vfs)
    passed = succ and 'import pdb' not in vfs.read('@ROOT/test_import.py')
    res.append(("Remove Import", passed, msg))
    return res