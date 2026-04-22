from typing import List, Tuple, Dict, Any

class EditToolV2:
    """
    Relative Delta Logic (Version 2).
    Calculates indentation difference between patch and file.
    """

    def _get_indent(self, line: str) -> int:
        """Returns the number of leading spaces."""
        return len(line) - len(line.lstrip())

    def _check_match_with_delta(self, original_lines: List[str], start_index: int, patch_lines: List[str]) -> Tuple[bool, int]:
        """
        Checks if patch_lines match original_lines starting at start_index using relative indentation.
        Returns (is_match, delta).
        """
        if start_index + len(patch_lines) > len(original_lines):
            return False, 0

        # Find anchor (first non-empty line in patch)
        anchor_idx = -1
        for i, line in enumerate(patch_lines):
            if line.strip():
                anchor_idx = i
                break
        
        if anchor_idx == -1:
            # Patch block is empty/whitespace only
            for i in range(len(patch_lines)):
                if original_lines[start_index + i].strip():
                    return False, 0
            return True, 0

        # Calculate Delta based on the anchor line
        patch_anchor = patch_lines[anchor_idx]
        file_anchor = original_lines[start_index + anchor_idx]
        
        if patch_anchor.strip() != file_anchor.strip():
            return False, 0
            
        patch_indent = self._get_indent(patch_anchor)
        file_indent = self._get_indent(file_anchor)
        delta = file_indent - patch_indent

        # Verify all lines satisfy the text match and the calculated delta
        for i, p_line in enumerate(patch_lines):
            f_line = original_lines[start_index + i]
            
            p_stripped = p_line.strip()
            f_stripped = f_line.strip()
            
            if p_stripped != f_stripped:
                return False, 0
            
            if p_stripped: 
                p_ind = self._get_indent(p_line)
                f_ind = self._get_indent(f_line)
                if f_ind != p_ind + delta:
                    return False, 0
        
        return True, delta

    def _apply_delta_to_block(self, block: str, delta: int) -> List[str]:
        """Applies the calculated indentation delta to the new block."""
        if not block: 
            return []
        
        lines = block.splitlines()
        new_lines = []
        for line in lines:
            if not line.strip():
                new_lines.append("")
                continue
            
            current_indent = self._get_indent(line)
            new_indent = max(0, current_indent + delta)
            stripped = line.lstrip()
            new_lines.append(" " * new_indent + stripped)
        return new_lines

    def _plan_replace_v2(self, original_lines: List[str], old_block: str, new_block: str) -> Dict[str, Any]:
        old_lines = old_block.splitlines()
        if not old_lines:
             return {"success": False, "message": "Block '---old---' cannot be empty."}

        for i in range(len(original_lines) - len(old_lines) + 1):
            match, delta = self._check_match_with_delta(original_lines, i, old_lines)
            if match:
                new_lines = self._apply_delta_to_block(new_block, delta)
                return {
                    "success": True, 
                    "start_line": i, 
                    "end_line": i + len(old_lines), 
                    "new_lines": new_lines, 
                    "message": f"Replacement planned (V2 Delta: {delta})."
                }
        
        return {"success": False, "message": "Specified '---old---' block not found (V2 Delta Matching)."}

    def _plan_insert_v2(self, original_lines: List[str], old_block_template: str, new_block: str, parts: list, add_blank_lines: bool) -> Dict[str, Any]:
        before_str = parts[0].strip('\r\n')
        after_str = parts[1].strip('\r\n')
        
        if not before_str and not after_str:
            return {"success": False, "message": "In -insert, the 'before' and 'after' markers cannot both be empty."}

        before_lines = before_str.splitlines() if before_str else []
        after_lines = after_str.splitlines() if after_str else []

        insert_idx = -1
        delta = 0

        if before_lines:
            for i in range(len(original_lines) - len(before_lines) + 1):
                match, d = self._check_match_with_delta(original_lines, i, before_lines)
                if match:
                    candidate_idx = i + len(before_lines)
                    if after_lines:
                        match_after, _ = self._check_match_with_delta(original_lines, candidate_idx, after_lines)
                        if match_after:
                            insert_idx = candidate_idx
                            delta = d
                            break
                    else:
                        insert_idx = candidate_idx
                        delta = d
                        break
        elif after_lines:
             for i in range(len(original_lines) - len(after_lines) + 1):
                match, d = self._check_match_with_delta(original_lines, i, after_lines)
                if match:
                    insert_idx = i
                    delta = d
                    break
        
        if insert_idx != -1:
            new_lines = self._apply_delta_to_block(new_block, delta)
            if add_blank_lines:
                new_lines = [""] + new_lines + [""]
            
            return {
                "success": True, 
                "start_line": insert_idx, 
                "end_line": insert_idx, 
                "new_lines": new_lines, 
                "message": f"Insertion planned (V2 Delta: {delta})."
            }

        return {"success": False, "message": "Insertion context not found (V2 Delta Matching)."}