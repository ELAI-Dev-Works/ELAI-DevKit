from typing import Tuple
from typing import List

def build_backup(args: list, content: str, project_root: str, backup_builder):
    from .utils import reconstruct_paths
    reconstructed_args = reconstruct_paths(args)
    if "to" not in reconstructed_args: return
    to_index = reconstructed_args.index("to")
    src_parts = [p for p in reconstructed_args[1:to_index] if p != "-dir"]
    dst_parts = reconstructed_args[to_index + 1:]
    if len(src_parts) != 1 or len(dst_parts) != 1: return
    
    src_path = src_parts[0]
    dst_path = dst_parts[0]
    
    is_dir = "-dir" in reconstructed_args
    backup_builder.use("replace", src_path)
    if is_dir:
        backup_builder.use("delete_dir", dst_path)
    else:
        backup_builder.use("delete", dst_path)

def run(args: list, content: str, fs) -> Tuple[bool, str]:
    from .utils import reconstruct_paths
    operation = "move"

    # Reconstruct paths to handle spaces correctly
    reconstructed_args = reconstruct_paths(args)

    if "to" not in reconstructed_args:
        return False, f"Operation {operation} does not have a 'to' destination specified."

    to_index = reconstructed_args.index("to")

    # Extract source and destination parts from the reconstructed list
    src_parts = [p for p in reconstructed_args[1:to_index] if p != "-dir"]
    dst_parts = reconstructed_args[to_index + 1:]

    if len(src_parts) != 1 or len(dst_parts) != 1:
        return False, "Invalid command format. Make sure paths are enclosed in quotation marks if they contain spaces."

    src_path = src_parts[0]
    dst_path = dst_parts[0]

    if not src_path or not dst_path:
        return False, "No source or destination specified."

    if not fs.exists(src_path):
        return False, f"Source not found: {fs._to_abs(src_path)}"

    fs.move(src_path, dst_path)
    return True, f"Move successful: {fs._to_abs(src_path)} -> {fs._to_abs(dst_path)}"

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    # Test file move
    vfs.write('@ROOT/move_src.txt', 'data')
    vfs.makedirs('@ROOT/move_dst_dir')
    succ, msg = run(['-move', '@ROOT/move_src.txt', 'to', '@ROOT/move_dst_dir'], '', vfs)
    passed = succ and vfs.exists('@ROOT/move_dst_dir/move_src.txt') and not vfs.exists('@ROOT/move_src.txt')
    res.append(("Move File", passed, msg))

    # Test directory move (VFS moves content INTO destination)
    vfs.makedirs('@ROOT/src_dir/sub')
    vfs.makedirs('@ROOT/dst_dir')
    succ, msg = run(['-move', '-dir', '@ROOT/src_dir', 'to', '@ROOT/dst_dir'], '', vfs)
    passed = succ and vfs.exists('@ROOT/dst_dir/sub') and not vfs.exists('@ROOT/src_dir')
    res.append(("Move Directory", passed, msg))
    return res