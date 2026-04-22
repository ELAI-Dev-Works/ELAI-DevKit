from typing import List, Tuple, Dict, Any
from .fuzzy_matching import find_best_match

def get_indent_level(line: str) -> int:
    """Returns the indentation level (number of leading spaces/tabs)."""
    return len(line) - len(line.lstrip(' \t'))

def find_scope_boundaries(original_lines: List[str], scope_block: str, threshold: float) -> Tuple[int, int, float]:
    """
    IMPROVED VERSION: Finds the start and end of a scope,
    using indentation to determine the end of a code block.
    Returns (start_index, end_index, match_ratio).
    Returns (-1, -1, ratio) if not found.
    """
    scope_start_index, scope_ratio = find_best_match(original_lines, scope_block, threshold)
    if scope_start_index == -1 or scope_ratio < threshold:
        return -1, -1, scope_ratio

    # Look for the first non-empty line in the block found to determine the base indentation.
    base_indent_level = -1
    first_line_index = -1
    scope_block_lines = scope_block.splitlines()
    
    # Find the first empty string in scope_block to determine its indentation in the original file
    for i in range(len(scope_block_lines)):
        if scope_block_lines[i].strip():
            # The index of the first significant line in the file
            first_line_index = scope_start_index + i
            # Indentation level of this line
            base_indent_level = get_indent_level(original_lines[first_line_index])
            break
            
    if base_indent_level == -1:
        # If the scope block is empty or consists only of spaces, we cannot define its boundaries.
        return -1, -1, scope_ratio

    # Now we're looking for the end of the area. The area ends when we meet.
    # a non-empty line with an indentation less than or equal to the base line.
    scope_end_index = len(original_lines) # By default, until the end of the file.
    # We begin the search with the line following the first line of our scope.
    for i in range(first_line_index + 1, len(original_lines)):
        line = original_lines[i]
        if line.strip(): # Ignoring empty lines
            current_indent_level = get_indent_level(line)
            if current_indent_level <= base_indent_level:
                scope_end_index = i
                break

    return scope_start_index, scope_end_index, scope_ratio