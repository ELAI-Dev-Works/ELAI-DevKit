import re
from typing import List, Dict, Any
from .tool_v1 import EditToolV1
from .tool_v2 import EditToolV2

class EditTool(EditToolV1, EditToolV2):
    """
    Unified Edit Tool supporting both V1 (Normalization) and V2 (Delta) strategies.
    Default strategy is V1. Use '-v2' flag in arguments to enable V2.
    """

    def plan_edit(self, args: list, content: str, original_content: str) -> Dict[str, Any]:
        if not args or len(args) < 2:
            return {"success": False, "message": "EDIT requires an argument and a file path."}
        
        command = args[0]
        use_v2 = '-v2' in args
        
        if "---new---" in content:
            parts = content.split("---new---", 1)
            old_block = parts[0].replace("---old---", "").strip('\r\n')
            new_block = parts[1].strip('\r\n')
        else:
            old_block = content.replace("---old---", "").strip('\r\n')
            new_block = ""
            
        original_lines = original_content.splitlines()
        
        if command in ("-replace", "-remove"):
            if use_v2:
                return self._plan_replace_v2(original_lines, old_block, new_block)
            else:
                return self._plan_replace_v1(original_lines, old_block, new_block)
                
        elif command == "-insert":
            # Parse markers first as they are needed for both V1 and V2
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
        else:
            return {"success": False, "message": f"Unknown argument for EDIT: {command}"}