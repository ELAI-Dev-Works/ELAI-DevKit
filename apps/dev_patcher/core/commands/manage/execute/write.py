from typing import Tuple
from typing import List
import os

def build_backup(args: list, content: str, project_root: str, backup_builder):
    path_args =[a for a in args[1:]]
    if not path_args: return
    path_str = ' '.join(path_args).strip('\'"')
    
    clean_path = path_str.replace('@ROOT/', '').replace('@ROOT\\', '').replace('@ROOT', '').strip('\'"')
    abs_path = os.path.join(project_root, clean_path)
    
    if os.path.exists(abs_path):
        backup_builder.use("replace", path_str)
    else:
        backup_builder.use("delete", path_str)

def run(args: list, content: str, fs) -> Tuple[bool, str]:
    path_args = [a for a in args[1:]]
    if not path_args:
        return False, "No path specified for the -write command."
    path_str = ' '.join(path_args).strip('\'"')

    if not fs.exists(path_str):
        return False, f"File to overwrite not found: {fs._to_abs(path_str)}."
    if fs.is_dir(path_str):
        return False, f"You can't use -write on a folder: {fs._to_abs(path_str)}."

    fs.write(path_str, content)
    return True, f"File successfully overwritten: {fs._to_abs(path_str)}"

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    vfs.write('@ROOT/test_write.txt', 'old')
    succ, msg = run(['-write', '@ROOT/test_write.txt'], 'new', vfs)
    passed = succ and vfs.read('@ROOT/test_write.txt') == 'new'
    res.append(("Write existing", passed, msg))

    succ, msg = run(['-write', '@ROOT/non_exist.txt'], 'new', vfs)
    passed = not succ and "not found" in msg
    res.append(("Write non-existing", passed, msg))
    return res