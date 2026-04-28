import re

def check_end_syntax(lines, lang):
    """
    Checks for malformed end markers.
    Examples caught: --end--, --- end ---, --end---
    """
    issues =[]
    pattern = re.compile(r"^(\s*)--+\s*end\s*--+\s*((?:\{!END\})?)", re.IGNORECASE)
    
    for i, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            whitespace = match.group(1)
            end_tag = match.group(2)
            
            correct_marker = f"{whitespace}---end---{end_tag}"
            orig_prefix = line[:match.end()]
            
            if orig_prefix != correct_marker:
                corrected_line = line.replace(orig_prefix, correct_marker, 1)
                issues.append({
                    "original": line,
                    "corrected": corrected_line,
                    "description": f"Malformed end marker. Should be '{correct_marker.strip()}'.",
                    "type": "syntax",
                    "start_line": i + 1
                })
    return issues