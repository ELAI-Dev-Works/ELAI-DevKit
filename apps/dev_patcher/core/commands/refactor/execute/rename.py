import os
from typing import Tuple, List, Set
from apps.dev_patcher.core.parser import PARSER # Import the shared Tree-sitter parser

def run(args: list, content: str, fs) -> Tuple[bool, str]:
    if not PARSER:
        return False, "Tree-sitter parser is not initialized. Cannot perform refactoring."

    # Parse arguments: -rename <Old> to <New>
    try:
        old_name_raw = args[1]
        to_keyword = args[2]
        new_name_raw = args[3]

        if not (old_name_raw.startswith('<') and old_name_raw.endswith('>')):
            return False, "Old name must be in <Brackets>."
        if to_keyword.lower() != "to":
            return False, "Syntax error. Expected 'to' after old name."
        if not (new_name_raw.startswith('<') and new_name_raw.endswith('>')):
            return False, "New name must be in <Brackets>."

        old_name = old_name_raw[1:-1]
        new_name = new_name_raw[1:-1]
    except IndexError:
        return False, "Invalid syntax. Use: -rename <Old> to <New>"

    is_project = "-project" in args
    has_ignore = "-ignore" in args

    # Parse Blocks
    files_to_scan = []
    ignore_list = set()

    if "---files---" in content:
        files_block = content.split("---files---")[1].split("---")[0].strip()
        files_to_scan = [f.strip() for f in files_block.splitlines() if f.strip()]

    if has_ignore and "---ignore---" in content:
        ignore_block = content.split("---ignore---")[1].split("---")[0].strip()
        ignore_list = {i.strip() for i in ignore_block.splitlines() if i.strip()}

    if is_project:
        # Scan entire project for .py files (currently only python supported by parser)
        files_to_scan = []
        for root, dirs, files in fs.walk(fs.root):
            if ".git" in dirs: dirs.remove(".git")
            if "__pycache__" in dirs: dirs.remove("__pycache__")
            for file in files:
                if file.endswith(".py"):
                    files_to_scan.append(os.path.join(root, file))
    elif not files_to_scan:
        return False, "No target files specified. Use -project or ---files--- block."

    modified_count = 0
    errors = []

    for file_path in files_to_scan:
        try:
            rel_path = os.path.relpath(file_path, fs.root).replace('\\', '/') if os.path.isabs(file_path) else file_path
            # Standardize to use FS read
            original_code = fs.read(rel_path)
            
            # AST Analysis
            tree = PARSER.parse(original_code.encode('utf8'))
            
            # Find all identifiers matching old_name
            # Tree-sitter query
            query_str = f"""
            (identifier) @id
            """
            # Python specific query might need adjustment depending on tree-sitter-python version,
            # but usually (identifier) covers variables, function names, class names usage.
            # Definition nodes are: (class_definition name: (identifier) @id), etc.
            
            # Simplification: We walk the tree manually to find nodes with matching text
            replacements = [] # (start_byte, end_byte, text)

            def traverse(node):
                if node.type == 'identifier':
                    node_text = original_code[node.start_byte:node.end_byte]
                    if node_text == old_name:
                        # Check ignore list
                        if node_text not in ignore_list: 
                             # Advanced ignore: check parent context if needed (future feature)
                             replacements.append((node.start_byte, node.end_byte))
                
                for child in node.children:
                    traverse(child)

            traverse(tree.root_node)

            if not replacements:
                continue

            # Apply replacements in reverse order
            replacements.sort(key=lambda x: x[0], reverse=True)
            
            code_bytes = bytearray(original_code.encode('utf8'))
            new_name_bytes = new_name.encode('utf8')

            for start, end in replacements:
                code_bytes[start:end] = new_name_bytes

            new_code = code_bytes.decode('utf8')
            fs.write(rel_path, new_code)
            modified_count += 1

        except Exception as e:
            errors.append(f"{file_path}: {str(e)}")

    msg = f"Renamed '{old_name}' to '{new_name}' in {modified_count} files."
    if errors:
        msg += f"\nErrors:\n" + "\n".join(errors)
    return True, msg

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    vfs.write('@ROOT/test_rename.py', 'def old_func():\n    pass\nold_func()')
    succ, msg = run(['-rename', '<old_func>', 'to', '<new_func>'], '---files---\n@ROOT/test_rename.py\n---', vfs)
    passed = succ and 'new_func' in vfs.read('@ROOT/test_rename.py')
    res.append(("Rename Function", passed, msg))
    return res
