import difflib
from typing import List, Tuple

def find_best_match(source_lines: List[str], target_block_str: str, threshold: float, start_search_from=0) -> Tuple[int, float]:
    """
    Finds the best 'fuzzy' match using optimizations for speed.
    """
    def get_code_signature(lines: List[str]) -> str:
        """Creates a single signature string from non-empty, cleared strings."""
        return "".join([line.strip() for line in lines if line.strip()])

    original_target_lines = target_block_str.splitlines()
    target_signature = get_code_signature(original_target_lines)

    if not target_signature:
        return -1, 0.0

    best_match_ratio = 0.0
    best_match_index = -1

    num_target_lines = len(original_target_lines)
    search_area = source_lines[start_search_from:]

    if not search_area or len(search_area) < num_target_lines:
        return -1, 0.0

    for i in range(len(search_area) - num_target_lines + 1):
        chunk_to_check = search_area[i : i + num_target_lines]
        chunk_signature = get_code_signature(chunk_to_check)

        if not chunk_signature:
            continue

        matcher = difflib.SequenceMatcher(None, target_signature, chunk_signature, autojunk=False)
        # Optimization: Quick_ratio works faster. If he's already below our best match, skip.
        if matcher.quick_ratio() < best_match_ratio:
            continue

        ratio = matcher.ratio()

        if ratio > best_match_ratio:
            best_match_ratio = ratio
            best_match_index = i + start_search_from

        # Optimization: If we find an almost perfect match, we can stop earlier.
        if ratio >= 0.999:
            break

    # After the cycle, best_match_ratio contains the highest similarity found.
    # Now we're checking to see if this best match meets the threshold.
    if best_match_ratio < threshold:
        # If not, return -1, but with the *actual* best ratio for an accurate error message.
        return -1, best_match_ratio

    # If it meets the threshold, return the index and the ratio.
    return best_match_index, best_match_ratio