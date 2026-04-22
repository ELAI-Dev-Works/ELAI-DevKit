import re
from typing import List, Tuple, Dict, Any

from ..commands.edit.tool import EditTool as StandardEditTool
from .extra.fuzzy_matching import find_best_match
from .extra.scope_matching import find_scope_boundaries

class Tool(StandardEditTool):
    """
    An extended version of EDIT that adds Fuzzy Matching and Scope Matching.
    Supports both V1 (Normalization) and V2 (Delta) strategies.
    """
    SIMILARITY_THRESHOLD = 0.70 # Fallback default

    def plan_edit(self, args: list, content: str, original_content: str, flags: dict = None) -> Dict[str, Any]:
        """
        Overridden planning method that supports Fuzzy and Scope Matching.
        """
        flags = flags or {}

        # --- Scope Matching Logic ---
        if flags.get('scope') and "---scope---" in content:
            try:
                parts = content.split("---scope---", 1)[1].split("---old---", 1)
                scope_block = parts[0].strip('\r\n')
                remaining_content = "---old---" + parts[1]
            except IndexError:
                return {"success": False, "message": "Parsing error ---scope--- and ---old---."}

            original_lines = original_content.splitlines()
            threshold = flags.get('threshold', self.SIMILARITY_THRESHOLD)

            scope_index, scope_end_index, scope_ratio = find_scope_boundaries(original_lines, scope_block, threshold)

            if scope_index == -1:
                return {"success": False, "message": f"Scope '---scope---' not found (similarity: {scope_ratio*100:.0f}%, threshold: {threshold*100:.0f}%)."}

            scoped_content_lines = original_lines[scope_index:scope_end_index]

            # Call the main handler, but with the reduced content and fuzzy flag enabled
            plan = self._plan_fuzzy_or_normal(args, remaining_content, "\n".join(scoped_content_lines), flags)

            if not plan.get('success'):
                plan['message'] += " (inside the found scope)"
                return plan

            # Adjust line numbers back to the original file context
            plan['start_line'] += scope_index
            plan['end_line'] += scope_index
            plan['message'] += f" in scope (similarity {scope_ratio*100:.0f}%)"
            return plan

        # --- Fallback to Fuzzy or Normal Logic ---
        return self._plan_fuzzy_or_normal(args, content, original_content, flags)

    def _plan_fuzzy_or_normal(self, args: list, content: str, original_content: str, flags: dict) -> Dict[str, Any]:
        """Internal method that chooses between fuzzy and normal search."""
        use_fuzzy = flags.get("fuzzy")
        use_v2 = '-v2' in args

        if "---new---" in content:
            parts = content.split("---new---", 1)
            old_block = parts[0].replace("---old---", "").strip('\r\n')
            new_block = parts[1].strip('\r\n')
        else:
            old_block = content.replace("---old---", "").strip('\r\n')
            new_block = ""

        command = args[0]
        original_lines = original_content.splitlines()

        if use_fuzzy:
            if command in ("-replace", "-remove"):
                return self._plan_fuzzy_replace(original_lines, old_block, new_block, flags, use_v2)
            elif command == "-insert":
                return self._plan_fuzzy_insert(original_lines, old_block, new_block, flags, use_v2)
        else:
            # Fallback to standard logic (V1 or V2 based on args)
            if command in ("-replace", "-remove"):
                if use_v2:
                    return self._plan_replace_v2(original_lines, old_block, new_block)
                else:
                    return self._plan_replace_v1(original_lines, old_block, new_block)
            elif command == "-insert":
                single_line_marker_re = r"\{code_start\|content\|code_end\}"
                multi_line_marker_re = r"\{code_start\}\s*\{content\}\s*\{code_end\}"
                
                is_single_line = re.search(single_line_marker_re, old_block)
                is_multi_line = not is_single_line and re.search(multi_line_marker_re, old_block, re.DOTALL)
                
                if is_single_line:
                    parts = re.split(single_line_marker_re, old_block, 1)
                    add_blank_lines = False
                elif is_multi_line:
                    parts = re.split(multi_line_marker_re, old_block, 1)
                    add_blank_lines = True
                else:
                    return {"success": False, "message": "For -insert, '---old---' must contain markers."}

                if use_v2:
                    return self._plan_insert_v2(original_lines, old_block, new_block, parts, add_blank_lines)
                else:
                    return self._plan_insert_v1(original_lines, old_block, new_block, parts, add_blank_lines)

        return {"success": False, "message": f"Unknown argument for EDIT: {command}"}

    def _plan_fuzzy_replace(self, original_lines: List[str], old_block: str, new_block: str, flags: dict = None, use_v2: bool = False) -> Dict[str, Any]:
        flags = flags or {}
        threshold = flags.get('threshold', self.SIMILARITY_THRESHOLD)
        match_index, match_ratio = find_best_match(original_lines, old_block, threshold)

        if match_index == -1 or match_ratio < threshold:
            return {"success": False, "message": f"Block '---old---' not found (similarity: {match_ratio*100:.0f}%, threshold: {threshold*100:.0f}%)"}

        num_old_lines = len(old_block.splitlines())

        if use_v2:
            # V2 Delta Logic
            # Find first non-empty line in old_block to act as anchor
            anchor_rel_idx = -1
            old_lines = old_block.splitlines()
            for i, line in enumerate(old_lines):
                if line.strip():
                    anchor_rel_idx = i
                    break
            
            delta = 0
            if anchor_rel_idx != -1:
                file_line_idx = match_index + anchor_rel_idx
                if file_line_idx < len(original_lines):
                    file_line = original_lines[file_line_idx]
                    patch_line = old_lines[anchor_rel_idx]
                    file_indent = self._get_indent(file_line)
                    patch_indent = self._get_indent(patch_line)
                    delta = file_indent - patch_indent
            
            new_lines = self._apply_delta_to_block(new_block, delta)
            return {
                "success": True,
                "start_line": match_index,
                "end_line": match_index + num_old_lines,
                "new_lines": new_lines,
                "message": f"Replacement is planned (Fuzzy V2: {match_ratio*100:.0f}%, Delta: {delta})"
            }
        else:
            # V1 Normalization Logic
            chunk_to_replace = original_lines[match_index : match_index + num_old_lines]
            indent_str = ""
            for line in chunk_to_replace:
                if line.strip():
                    indent_str = line[:len(line) - len(line.lstrip(' \t'))]
                    break

            norm_new_lines = self._normalize_lines(new_block) if new_block else []
            indented_new_lines = [(indent_str + line) for line in norm_new_lines]

            return {
                "success": True,
                "start_line": match_index,
                "end_line": match_index + num_old_lines,
                "new_lines": indented_new_lines,
                "message": f"Replacement is planned (Fuzzy V1: {match_ratio*100:.0f}%)"
            }

    def _plan_fuzzy_insert(self, original_lines: List[str], old_block_template: str, new_block: str, flags: dict = None, use_v2: bool = False) -> Dict[str, Any]:
        """ Fuzzy version of _plan_insert. """
        flags = flags or {}
        threshold = flags.get('threshold', self.SIMILARITY_THRESHOLD)
        single_line_marker_re = r"\{code_start\|content\|code_end\}"
        multi_line_marker_re = r"\{code_start\}\s*\{content\}\s*\{code_end\}"

        is_single_line = re.search(single_line_marker_re, old_block_template)
        is_multi_line = not is_single_line and re.search(multi_line_marker_re, old_block_template)

        if is_single_line:
            parts = re.split(single_line_marker_re, old_block_template, 1)
            add_blank_lines = False
        elif is_multi_line:
            parts = re.split(multi_line_marker_re, old_block_template, 1)
            add_blank_lines = True
        else:
            return {"success": False, "message": "For -insert, '---old---' must contain markers."}

        before_str = parts[0].strip('\r\n')
        after_str = parts[1].strip('\r\n')

        if not before_str and not after_str:
            return {"success": False, "message": "In -insert, the 'before' and 'after' markers cannot both be empty."}

        insert_line_index = -1
        before_match_ratio = 0
        after_match_ratio = 0
        
        # For V2 delta calculation
        match_start_index_for_delta = -1
        matched_block_str = None

        if before_str:
            before_idx, before_ratio = find_best_match(original_lines, before_str, threshold)
            if before_idx == -1 or before_ratio < threshold:
                return {"success": False, "message": f"Context 'before' for -insert not found (similarity: {before_ratio*100:.0f}%, threshold: {threshold*100:.0f}%)"}

            insert_line_index = before_idx + len(before_str.splitlines())
            before_match_ratio = before_ratio
            match_start_index_for_delta = before_idx
            matched_block_str = before_str

            if after_str:
                after_idx, after_ratio = find_best_match(original_lines, after_str, threshold, start_search_from=insert_line_index)
                if after_idx == -1 or after_ratio < threshold:
                     return {"success": False, "message": f"No 'after' context for -insert found after 'before' block (similarity: {after_ratio*100:.0f}%, threshold: {threshold*100:.0f}%)"}
                after_match_ratio = after_ratio

        elif after_str:
            after_idx, after_ratio = find_best_match(original_lines, after_str, threshold)
            if after_idx == -1 or after_ratio < threshold:
                 return {"success": False, "message": f"Context 'after' for -insert not found (similarity: {after_ratio*100:.0f}%, threshold: {threshold*100:.0f}%)"}

            insert_line_index = after_idx
            after_match_ratio = after_ratio
            match_start_index_for_delta = after_idx
            matched_block_str = after_str

        if insert_line_index != -1:
            if use_v2:
                # Calculate delta based on the matched block (before or after)
                delta = 0
                if matched_block_str:
                    ref_lines = matched_block_str.splitlines()
                    for i, line in enumerate(ref_lines):
                        if line.strip():
                            file_line_idx = match_start_index_for_delta + i
                            if file_line_idx < len(original_lines):
                                file_line = original_lines[file_line_idx]
                                file_indent = self._get_indent(file_line)
                                patch_indent = self._get_indent(line)
                                delta = file_indent - patch_indent
                                break
                
                new_lines = self._apply_delta_to_block(new_block, delta)
                if add_blank_lines:
                    new_lines = [""] + new_lines + [""]
                
                plan = {
                    "success": True, 
                    "start_line": insert_line_index, 
                    "end_line": insert_line_index, 
                    "new_lines": new_lines
                }
            else:
                plan = self._build_insert_plan_v1(new_block, add_blank_lines, before_str, after_str, insert_line_index)
            
            plan['message'] = f"The insertion is planned (Fuzzy Match: before={before_match_ratio*100:.0f}%, after={after_match_ratio*100:.0f}%)"
            return plan

        return {"success": False, "message": "Unable to find insertion point using Fuzzy Matching."}