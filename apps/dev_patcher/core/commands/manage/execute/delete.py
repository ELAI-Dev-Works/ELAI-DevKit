from typing import Tuple
from typing import List

def build_backup(args: list, content: str, project_root: str, backup_builder):
    path_args = [a for a in args[1:] if a != "-dir"]
    if not path_args: return
    path_str = ' '.join(path_args).strip('\'"')
    backup_builder.use("replace", path_str)

def run(args: list, content: str, fs) -> Tuple[bool, str]:
    path_args =[a for a in args[1:] if a != "-dir"]
    if not path_args:
        return False, "The path to delete is not specified."

    target_path = ' '.join(path_args).strip('\'"')

    if not fs.exists(target_path):
        return False, f"Object to delete not found: {fs._to_abs(target_path)}"

    fs.delete(target_path)
    return True, f"Object removed: {fs._to_abs(target_path)}"

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    vfs.write('@ROOT/test_del.txt', 'data')
    succ, msg = run(['-delete', '@ROOT/test_del.txt'], '', vfs)
    passed = succ and not vfs.exists('@ROOT/test_del.txt')
    res.append(("Delete File", passed, msg))

    vfs.makedirs('@ROOT/test_dir_del')
    succ, msg = run(['-delete', '-dir', '@ROOT/test_dir_del'], '', vfs)
    passed = succ and not vfs.exists('@ROOT/test_dir_del')
    res.append(("Delete Dir", passed, msg))
    return res