import os
import re
from typing import Tuple, Optional
from apps.dev_patcher.core.parser import PARSER

def run(args: list, content: str, fs) -> Tuple[bool, str]:
    if not PARSER:
        return False, "Tree-sitter parser is not initialized."

    # --- 1. Argument Parsing ---
    def get_arg_val(key):
        try:
            return args[args.index(key) + 1]
        except (ValueError, IndexError):
            return None

    # Arguments
    # -type: what we insert (class/func) -> affects spacing
    # -search_type: scope limit (code/class/func) -> currently implicit in anchors, but can be used for start/end
    # -pos: <top:A|bottom:B> or <start> or <end>
    
    search_type = get_arg_val("-search_type")
    # Expected format for -search_type if we want to scope to a class: "class MyClass" or just "class" (if only one)
    # But usually <start/end> implies we are inside a specific scope.
    # To keep it compatible with -pos <top...>, we reuse find_node_by_def logic if a name is needed.

    inject_type = get_arg_val("-type") or "code"
    pos_arg = get_arg_val("-pos")

    if not pos_arg:
        return False, "Missing required argument: -pos <...>"

    if not (pos_arg.startswith('<') and pos_arg.endswith('>')):
        return False, "-pos argument must be enclosed in <...>"

    pos_val = pos_arg[1:-1]

    # Content Parsing
    if "---content---" not in content:
        return False, "Missing ---content--- block."

    parts = content.split("---content---")
    header_part = parts[0]
    code_to_inject = parts[1].strip('\r\n')

    # File Parsing
    files_to_scan = []
    if "---files---" in header_part:
        files_block = header_part.split("---files---")[1].split("---")[0].strip()
        files_to_scan = [f.strip() for f in files_block.splitlines() if f.strip()]

    if not files_to_scan:
        return False, "No files specified in ---files--- block."

    # --- 2. Anchor Logic Setup ---
    top_anchor_def = None
    bottom_anchor_def = None
    position_mode = "relative" # relative, start, end

    if pos_val in ["start", "end"]:
        position_mode = pos_val
    else:
        # Parse top/bottom
        sub_parts = pos_val.split('|')
        for p in sub_parts:
            p = p.strip()
            if p.lower().startswith("top:"):
                top_anchor_def = p[4:].strip() 
            elif p.lower().startswith("bottom:"):
                bottom_anchor_def = p[7:].strip()

    modified_count = 0
    errors = []

    # Helper to find a node by type and name
    def find_node_by_def(parent_node, def_string, source_bytes):
        parts = def_string.split()
        if len(parts) < 2: return None

        target_type_map = {
            'class': 'class_definition',
            'def': 'function_definition',
            'async': 'function_definition'
        }

        target_keyword = parts[0]
        target_name = parts[1]
        ts_type = target_type_map.get(target_keyword)
        if not ts_type: return None

        # DFS/BFS for finding the node - simplified to direct children for now
        # but for search_type we might want deeper search if it's not root
        for child in parent_node.children:
            if child.type == ts_type:
                name_node = child.child_by_field_name('name')
                if name_node:
                    actual_name = source_bytes[name_node.start_byte:name_node.end_byte].decode('utf8')
                    if actual_name == target_name:
                        return child
        return None

    # --- 3. Processing Files ---
    for file_path in files_to_scan:
        try:
            rel_path = os.path.relpath(file_path, fs.root).replace('\\', '/') if os.path.isabs(file_path) else file_path

            if not fs.exists(rel_path):
                errors.append(f"File not found: {rel_path}")
                continue

            original_code = fs.read(rel_path)
            code_bytes = original_code.encode('utf8')
            tree = PARSER.parse(code_bytes)
            root_node = tree.root_node

            insertion_point = -1
            base_indent = ""
            
            # --- Scope Resolution ---
            target_scope = root_node
            
            # If search_type provided (e.g. -search_type <class MyClass>), find that scope
            if search_type and search_type.startswith('<') and search_type.endswith('>'):
                scope_def = search_type[1:-1]
                found_scope = find_node_by_def(root_node, scope_def, code_bytes)
                if found_scope:
                    target_scope = found_scope
                    # Update base indent for the scope
                    lines = original_code.splitlines()
                    scope_line = lines[found_scope.start_point[0]]
                    # Scope indent + 1 level (4 spaces)
                    scope_indent = scope_line[:len(scope_line) - len(scope_line.lstrip())]
                    base_indent = scope_indent + "    " 
                else:
                    errors.append(f"{rel_path}: Scope '{scope_def}' not found.")
                    continue

            # --- Insertion Point Calculation ---
            found_anchor = None # For indentation reference

            if position_mode == "start":
                # Insert at the beginning of the scope body
                # For class/def, body is usually a 'block' node
                body_node = target_scope.child_by_field_name('body')
                if body_node:
                    insertion_point = body_node.start_point[0] + 1 # After the colon/docstring check?
                    # Simple approach: start of body
                    # If docstring exists, maybe skip it? (Advanced TODO)
                    found_anchor = body_node
                else:
                    # Fallback for module level
                    insertion_point = 0 
                    
            elif position_mode == "end":
                # Insert at the end of the scope
                if target_scope == root_node:
                    insertion_point = len(original_code.splitlines())
                else:
                    insertion_point = target_scope.end_point[0]
                    found_anchor = target_scope

            else: # Relative mode (anchors)
                t_node = find_node_by_def(target_scope, top_anchor_def, code_bytes) if top_anchor_def else None
                b_node = find_node_by_def(target_scope, bottom_anchor_def, code_bytes) if bottom_anchor_def else None

                if t_node:
                    insertion_point = t_node.end_point[0] + 1
                    found_anchor = t_node
                elif b_node:
                    insertion_point = b_node.start_point[0]
                    found_anchor = b_node

            if insertion_point == -1:
                errors.append(f"{rel_path}: Insertion point could not be determined.")
                continue

            # Determine Indentation (Refined)
            lines = original_code.splitlines()
            if found_anchor and not base_indent:
                # If we haven't set base_indent from scope, try anchor
                # But if anchor is inside the scope, its indent is what we want for SIBLINGS
                anchor_line = lines[found_anchor.start_point[0]]
                base_indent = anchor_line[:len(anchor_line) - len(anchor_line.lstrip())]

            # Determine Spacing
            # If injecting a class/func at root level, we typically want 2 empty lines
            # If inside a class, 1 empty line
            # We can guess "root level" if base_indent is empty
            
            prefix_newlines = []
            suffix_newlines = []
            
            is_root = (base_indent == "")
            gap = 2 if (is_root and inject_type in ['class', 'func']) else 1
            
            prefix_newlines = [""] * gap
            suffix_newlines = [""] * gap

            # --- Construct New Content ---
            new_lines = []
            new_lines.extend(prefix_newlines)
            
            # Apply indentation to injected code
            for line in code_to_inject.splitlines():
                if line.strip():
                    new_lines.append(base_indent + line)
                else:
                    new_lines.append("")
            
            new_lines.extend(suffix_newlines)

            # Insert into lines
            # insertion_point is a 0-based index of the line *where insertion begins*
            # lines list manipulation
            
            # Check bounds
            if insertion_point > len(lines):
                insertion_point = len(lines)
                
            lines[insertion_point:insertion_point] = new_lines
            
            # Write back
            fs.write(rel_path, "\n".join(lines))
            modified_count += 1

        except Exception as e:
            import traceback
            errors.append(f"{file_path}: {e}")

    msg = f"Injection completed in {modified_count} files."
    if errors:
        msg += f"\nErrors:\n" + "\n".join(errors)
    
    return True, msg

from typing import List

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    vfs.write('@ROOT/test_inject.py', 'class MyClass:\n    def method(self):\n        pass\n')
    content = "---files---\n@ROOT/test_inject.py\n---\n---content---\n    def new_method(self):\n        pass"
    succ, msg = run(['-inject', '-type', 'func', '-search_type', '<class MyClass>', '-pos', '<end>'], content, vfs)
    passed = succ and 'new_method' in vfs.read('@ROOT/test_inject.py')
    res.append(("Inject Method", passed, msg))
    return res
