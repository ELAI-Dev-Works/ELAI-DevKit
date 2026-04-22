import re
from typing import List, Tuple, Set
from tree_sitter_language_pack import get_parser

def initialize_parser():
    """Initializes the parser using the pre-built grammar from tree-sitter-language-pack."""
    try:
        parser = get_parser("python")
        print("The tree-sitter parser has been successfully initialized.")
        return parser
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to get parser: {e}")
        return None

PARSER = initialize_parser()

def get_all_ignored_lines(text: str) -> Set[int]:
    """
    Creates a complete set of all ignored lines by combining tree-sitter and manual checking.
    """
    if not PARSER:
        return set()

    # --- Stage 1: Get standard strings and comments from tree-sitter ---
    ignored_lines = set()
    text_as_bytes = text.encode('utf8')
    tree = PARSER.parse(text_as_bytes)

    # Recursive function to traverse the tree and find the necessary nodes
    def find_nodes_by_type(node, types, collection):
        if node.type in types:
            # tree-sitter uses 0-based indexing, we use 1-based indexing
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            for i in range(start_line, end_line + 1):
                collection.add(i)

        for child in node.children:
            find_nodes_by_type(child, types, collection)

    find_nodes_by_type(tree.root_node, {"string", "comment"}, ignored_lines)

    # --- Stage 2: Add our custom comments ---
    lines = text.splitlines()
    in_multiline_comment = False
    for i, line in enumerate(lines):
        line_num = i + 1
        stripped_line = line.strip()

        # Multiline comments #@# ... #@#
        if in_multiline_comment:
            ignored_lines.add(line_num)
            if stripped_line == "#@#":
                in_multiline_comment = False
            continue
        if stripped_line == "#@#":
            ignored_lines.add(line_num)
            in_multiline_comment = True
            continue

        # Single-line comments <-@ ... @->
        if stripped_line.startswith("<-@") and stripped_line.endswith("@->"):
            ignored_lines.add(line_num)

    return ignored_lines

def _strip_line_number(line: str) -> str:
    """
    Checks if a line starts with a number (e.g., '  12| '), and if so,
    removes that part, preserving the original indentation that follows.
    """
    # Search for the pattern: (optional spaces)(digits)(optional spaces)|(optional space)
    match = re.match(r"^\s*\d+\s*\|\s?", line)
    if match:
        # Return the rest of the string after the matched pattern
        return line[match.end():]
    return line

def parse_patch_content(text: str, experimental_flags: dict = None) -> List[Tuple[str, List[str], str]]:
    """
    Parses the input text using a more robust approach that correctly
    handles complex multi-line commands.
    """
    if not PARSER:
        return []

    lines = text.splitlines()
    commands = []
    ignored_lines = get_all_ignored_lines(text)

    use_lineno_stripping = (
        experimental_flags and
        experimental_flags.get("enabled") and
        experimental_flags.get("lineno")
    )

    i = 0
    while i < len(lines):
        line_num = i + 1
        line = lines[i]
        stripped_line = line.strip()

        if line_num in ignored_lines:
            i += 1
            continue

        is_raw_mode = stripped_line.startswith("{!RUN}<@|")
        is_smart_mode = stripped_line.startswith("<@|")

        if is_raw_mode or is_smart_mode:
            # --- Command header detected ---
            if is_raw_mode:
                header = stripped_line.replace("{!RUN}<@|", "")
            else: # is_smart_mode
                header = stripped_line.replace("<@|", "")

            parts = header.split()
            command_name = parts[0]
            args = parts[1:]

            content_lines = []
            j = i + 1
            while j < len(lines):
                content_line = lines[j]
                content_line_num = j + 1
                stripped_content_line = content_line.strip()

                # --- Check for the end marker ---
                is_raw_end = is_raw_mode and stripped_content_line.endswith("---end---{!END}")
                is_smart_end = not is_raw_mode and stripped_content_line.startswith("---end---") and content_line_num not in ignored_lines

                if is_raw_end:
                    # In Raw mode, capture content up to the marker
                    end_marker_pos = content_line.rfind("---end---{!END}")
                    if end_marker_pos > 0:
                        content_lines.append(content_line[:end_marker_pos])
                    i = j # Move the main cursor past the command block
                    break
                elif is_smart_end:
                    i = j # Move the main cursor past the command block
                    break

                # If it's not the end marker, add the line to the content
                content_lines.append(content_line)
                j += 1
            else: # The loop finished without finding an end marker
                i = j

            # --- Process and save the command ---
            if use_lineno_stripping and is_smart_mode:
                processed_lines = [_strip_line_number(l) for l in content_lines]
                content = "\n".join(processed_lines)
            else:
                content = "\n".join(content_lines)

            commands.append((command_name, args, content))

        i += 1

    return commands