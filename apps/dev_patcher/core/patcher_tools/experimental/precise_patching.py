import re
from typing import Dict, Any
from ..extra_tool import Tool as ExtraTool
from apps.dev_patcher.core.parser import _strip_line_number

class Tool(ExtraTool):
    """
    Experimental version of EDIT that adds Precise Patching (line number handling).
    Inherits Fuzzy and Scope Matching from ExtraTool.
    """
    def plan_edit(self, args: list, content: str, original_content: str, flags: dict = None) -> Dict[str, Any]:
        """
        Plans an edit, preprocessing line numbers if the 'lineno' flag is active.
        """
        flags = flags or {}
        if not flags.get('lineno'):
            # If the flag is not active, pass control to the parent class
            return super().plan_edit(args, content, original_content, flags)

        # --- Line number processing logic ---
        # Extract the scope, if it exists, so it doesn't interfere with further processing
        scope_prefix = ""
        core_content = content
        if flags.get('scope') and "---scope---" in content:
            # Split the content into scope and the remaining part
            content_parts = content.split("---old---", 1)
            scope_part_raw = content_parts[0] # Everything before ---old---
            core_content = "---old---" + content_parts[1] # ---old--- and everything after
            # Remove ---scope--- from the scope part for a clean reassembly
            scope_prefix = scope_part_raw.replace("---scope---", "---scope---\n")


        # Split the main part of the content into ---old--- and ---new---
        if "---new---" in core_content:
            parts = core_content.split("---new---", 1)
            old_block_raw = parts[0].replace("---old---", "").strip('\r\n')
            new_block_raw = parts[1].strip('\r\n')

            processed_old = "\n".join([_strip_line_number(l) for l in old_block_raw.splitlines()])
            processed_new = "\n".join([_strip_line_number(l) for l in new_block_raw.splitlines()])

            processed_core_content = f"---old---\n{processed_old}\n---new---\n{processed_new}"
        else: # Case for -remove
            old_block_raw = core_content.replace("---old---", "").strip('\r\n')
            processed_old = "\n".join([_strip_line_number(l) for l in old_block_raw.splitlines()])
            processed_core_content = f"---old---\n{processed_old}"

        # Reconnect the scope back with the processed content
        processed_content = scope_prefix + processed_core_content
        
        # Call the parent plan_edit (from ExtraTool) with the cleaned content
        plan = super().plan_edit(args, processed_content, original_content, flags)
        
        if plan.get('success'):
            plan['message'] += " (Precise Patching)"

        return plan