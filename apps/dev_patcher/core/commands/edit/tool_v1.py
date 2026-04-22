from typing import List, Dict, Any

class EditToolV1:
    """
    Legacy Normalization Logic (Version 1).
    Strips common indentation to zero to match blocks regardless of nesting depth.
    """

    def _normalize_lines(self, block: str) -> List[str]:
        lines = block.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]
        if not non_empty_lines:
            return [""] * len(lines)
        min_indent = min(len(line) - len(line.lstrip(' \t')) for line in non_empty_lines)
        normalized_lines = []
        for line in lines:
            if line.strip():
                normalized_lines.append(line[min_indent:])
            else:
                normalized_lines.append("")
        return normalized_lines

    def _plan_replace_v1(self, original_lines: List[str], old_block: str, new_block: str) -> Dict[str, Any]:
        old_block_lines_list = old_block.splitlines()
        if not old_block_lines_list:
            return {"success": False, "message": "Block '---old---' cannot be empty for replace/remove."}
        
        num_old_lines = len(old_block_lines_list)
        norm_old_block = self._normalize_lines(old_block)
        
        for i in range(len(original_lines) - num_old_lines + 1):
            chunk_to_check = original_lines[i : i + num_old_lines]
            if self._normalize_lines('\n'.join(chunk_to_check)) == norm_old_block:
                indent_str = ""
                if i > 0:
                    prev_line = original_lines[i - 1]
                    if prev_line.strip():
                        indent_str = prev_line[:len(prev_line) - len(prev_line.lstrip(' \t'))]
                    else:
                        for j in range(i - 2, -1, -1):
                            context_line = original_lines[j]
                            if context_line.strip():
                                indent_str = context_line[:len(context_line) - len(context_line.lstrip(' \t'))]
                                break
                if not indent_str:
                    for line in chunk_to_check:
                        if line.strip():
                            indent_str = line[:len(line) - len(line.lstrip(' \t'))]
                            break
                
                norm_new_lines = self._normalize_lines(new_block) if new_block else []
                indented_new_lines = [(indent_str + line) for line in norm_new_lines]
                return {"success": True, "start_line": i, "end_line": i + num_old_lines, "new_lines": indented_new_lines, "message": "Replacement planned (V1 Normalization)."}
        return {"success": False, "message": "Specified '---old---' block not found (V1)."}

    def _plan_insert_v1(self, original_lines: List[str], old_block_template: str, new_block: str, parts: list, add_blank_lines: bool) -> Dict[str, Any]:
        before_str = parts[0].strip('\r\n')
        after_str = parts[1].strip('\r\n')
        
        if not before_str and not after_str:
            return {"success": False, "message": "In -insert, the 'before' and 'after' markers cannot both be empty."}
        
        norm_before_lines = self._normalize_lines(before_str)
        norm_after_lines = self._normalize_lines(after_str)
        
        if norm_before_lines:
            for i in range(len(original_lines) - len(norm_before_lines) + 1):
                chunk_before = original_lines[i : i + len(norm_before_lines)]
                if self._normalize_lines('\n'.join(chunk_before)) == norm_before_lines:
                    insert_line_index = i + len(norm_before_lines)
                    if not norm_after_lines:
                        return self._build_insert_plan_v1(new_block, add_blank_lines, before_str, after_str, insert_line_index)
                    search_from_index = insert_line_index
                    for j in range(search_from_index, len(original_lines) - len(norm_after_lines) + 1):
                        chunk_after = original_lines[j : j + len(norm_after_lines)]
                        if self._normalize_lines('\n'.join(chunk_after)) == norm_after_lines:
                            return self._build_insert_plan_v1(new_block, add_blank_lines, before_str, after_str, insert_line_index)
        elif norm_after_lines:
            for i in range(len(original_lines) - len(norm_after_lines) + 1):
                chunk_after = original_lines[i : i + len(norm_after_lines)]
                if self._normalize_lines('\n'.join(chunk_after)) == norm_after_lines:
                    insert_line_index = i
                    return self._build_insert_plan_v1(new_block, add_blank_lines, before_str, after_str, insert_line_index)
                    
        return {"success": False, "message": "The pattern for insertion point ('---old---') was not found (V1)."}

    def _build_insert_plan_v1(self, new_block: str, add_blank_lines: bool, before_context_str: str, after_context_str: str, insert_line_index: int) -> Dict[str, Any]:
        indent_str = ""
        before_lines = before_context_str.splitlines()
        after_lines = after_context_str.splitlines()
        
        last_before_line = next((line for line in reversed(before_lines) if line.strip()), None)
        first_after_line = next((line for line in after_lines if line.strip()), None)
        
        get_indent = lambda line: line[:len(line) - len(line.lstrip(' \t'))] if line else ""
        
        indent_before = get_indent(last_before_line)
        indent_after = get_indent(first_after_line)
        
        if last_before_line and first_after_line:
            if len(indent_after) < len(indent_before):
                indent_str = indent_after
            else:
                indent_str = indent_before
        elif last_before_line:
            indent_str = indent_before
        elif first_after_line:
            indent_str = indent_after
            
        norm_new_lines = self._normalize_lines(new_block)
        indented_new_lines = [(indent_str + line).rstrip('\r\n') for line in norm_new_lines]
        
        if add_blank_lines:
            final_new_lines = [indent_str] + indented_new_lines + [indent_str]
        else:
            final_new_lines = indented_new_lines
            
        return {"success": True, "start_line": insert_line_index, "end_line": insert_line_index, "new_lines": final_new_lines, "message": "Insertion successfully scheduled (V1)."}