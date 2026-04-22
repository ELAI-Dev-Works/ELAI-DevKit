from typing import Tuple
from typing import List
import os

def build_backup(args: list, content: str, project_root: str, backup_builder):
    is_dir = "-dir" in args
    path_args = [a for a in args[1:] if a != "-dir"]
    if not path_args: return
    path_str = ' '.join(path_args).strip('\'"')
    
    clean_path = path_str.replace('@ROOT/', '').replace('@ROOT\\', '').replace('@ROOT', '').strip('\'"')
    abs_path = os.path.join(project_root, clean_path)
    
    if not os.path.exists(abs_path):
        if is_dir:
            backup_builder.use("delete_dir", path_str)
        else:
            backup_builder.use("delete", path_str)
    else:
        backup_builder.use("replace", path_str)

def run(args: list, content: str, fs) -> Tuple[bool, str]:
    is_dir = "-dir" in args
    path_args = [a for a in args[1:] if a != "-dir"]
    if not path_args:
        return False, "The path to create is not specified."

    path_str = ' '.join(path_args).strip('\'"')

    if is_dir:
        fs.makedirs(path_str)
        return True, f"Folder created: {fs._to_abs(path_str)}"
    else:
        if fs.exists(path_str):
            return False, f"File already exists: {fs._to_abs(path_str)}. Use -write to overwrite."
        fs.write(path_str, content)
        return True, f"File created: {fs._to_abs(path_str)}"

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    succ, msg = run(['-create', '@ROOT/test_create.txt'], 'content', vfs)
    passed = succ and vfs.exists('@ROOT/test_create.txt') and vfs.read('@ROOT/test_create.txt') == 'content'
    res.append(("Create File", passed, msg if not passed else ""))

    succ, msg = run(['-create', '-dir', '@ROOT/test_dir'], '', vfs)
    passed = succ and vfs.is_dir('@ROOT/test_dir')
    res.append(("Create Dir", passed, msg if not passed else ""))

    succ, msg = run(['-create', '@ROOT/test_create.txt'], 'new', vfs)
    passed = not succ and "already exists" in msg
    res.append(("Prevent Overwrite", passed, "Should have failed with exists error" if succ else ""))

    return res