from typing import Tuple
from typing import List

def build_backup(args: list, content: str, project_root: str, backup_builder):
    if "as" not in args: return
    as_index = args.index("as")
    old_name_parts =[p for p in args[1:as_index] if p != "-dir"]
    new_name_parts = args[as_index + 1:]
    if not old_name_parts or not new_name_parts: return
    
    old_path = ' '.join(old_name_parts).strip('\'"')
    new_path = ' '.join(new_name_parts).strip('\'"')
    
    is_dir = "-dir" in args
    backup_builder.use("replace", old_path)
    if is_dir:
        backup_builder.use("delete_dir", new_path)
    else:
        backup_builder.use("delete", new_path)

def run(args: list, content: str, fs) -> Tuple[bool, str]:
    if "as" not in args:
        return False, "No new name 'as' was specified for the -rename operation."
    as_index = args.index("as")
    old_name_parts = [p for p in args[1:as_index] if p != "-dir"]
    new_name_parts = args[as_index + 1:]

    if not old_name_parts or not new_name_parts:
        return False, "The old or new path is not specified."

    old_path = ' '.join(old_name_parts).strip('\'"')
    new_path = ' '.join(new_name_parts).strip('\'"')

    if not fs.exists(old_path):
        return False, f"Object to rename not found: {fs._to_abs(old_path)}"

    fs.rename(old_path, new_path)
    return True, f"Renamed: {fs._to_abs(old_path)} -> {fs._to_abs(new_path)}"

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    # Test file rename
    vfs.write('@ROOT/old_name.txt', 'data')
    succ, msg = run(['-rename', '@ROOT/old_name.txt', 'as', '@ROOT/new_name.txt'], '', vfs)
    passed = succ and vfs.exists('@ROOT/new_name.txt') and not vfs.exists('@ROOT/old_name.txt')
    res.append(("Rename File", passed, msg))

    # Test directory rename
    vfs.makedirs('@ROOT/old_dir_name')
    succ, msg = run(['-rename', '-dir', '@ROOT/old_dir_name', 'as', '@ROOT/new_dir_name'], '', vfs)
    passed = succ and vfs.exists('@ROOT/new_dir_name') and not vfs.exists('@ROOT/old_dir_name')
    res.append(("Rename Directory", passed, msg))
    return res