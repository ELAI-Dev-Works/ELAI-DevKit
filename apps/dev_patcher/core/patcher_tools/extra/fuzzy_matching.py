import difflib
from typing import List, Tuple

def get_code_signature(lines: List[str]) -> str:
    """Creates a single signature string from non-empty, cleared strings."""
    return "".join([line.strip() for line in lines if line.strip()])

def _fuzzy_chunk_worker(search_area: List[str], target_signature: str, num_target_lines: int, start_offset: int, threshold: float) -> Tuple[int, float]:
    best_match_ratio = 0.0
    best_match_index = -1
    for i in range(len(search_area) - num_target_lines + 1):
        chunk_to_check = search_area[i : i + num_target_lines]
        chunk_signature = get_code_signature(chunk_to_check)
        if not chunk_signature:
            continue

        matcher = difflib.SequenceMatcher(None, target_signature, chunk_signature, autojunk=False)
        if matcher.quick_ratio() < best_match_ratio:
            continue

        ratio = matcher.ratio()
        if ratio > best_match_ratio:
            best_match_ratio = ratio
            best_match_index = i + start_offset
        if ratio >= 0.999:
            break

    return best_match_index, best_match_ratio

def find_best_match(source_lines: List[str], target_block_str: str, threshold: float, start_search_from=0) -> Tuple[int, float]:
    """
    Finds the best 'fuzzy' match sequentially (avoids GIL bottleneck).
    """
    original_target_lines = target_block_str.splitlines()
    target_signature = get_code_signature(original_target_lines)

    if not target_signature:
        return -1, 0.0

    num_target_lines = len(original_target_lines)
    search_area = source_lines[start_search_from:]

    if not search_area or len(search_area) < num_target_lines:
        return -1, 0.0

    # Run sequentially. difflib is CPU bound, ThreadPool makes it slower due to GIL.
    best_match_index, best_match_ratio = _fuzzy_chunk_worker(search_area, target_signature, num_target_lines, start_search_from, threshold)

    if best_match_ratio < threshold:
        return -1, best_match_ratio

    return best_match_index, best_match_ratio