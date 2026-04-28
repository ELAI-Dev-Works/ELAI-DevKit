import re

def check_command_syntax(lines, lang):
    """
    Checks for malformed or incorrectly cased command markers.
    Examples caught: <@EDIT, <@ edit, <@|edit
    """
    issues =[]
    # Captures optional leading whitespace, optional {!RUN}, and the command name
    pattern = re.compile(r"^(\s*)((?:\{!RUN\})?)\s*<\s*@\s*\|?\s*([A-Za-z_]+)", re.IGNORECASE)
    
    for i, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            whitespace = match.group(1)
            run_tag = match.group(2)
            cmd_name = match.group(3)
            
            correct_marker = f"{whitespace}{run_tag}<@|{cmd_name.upper()}"
            orig_prefix = line[:match.end()]

            if orig_prefix != correct_marker:
                corrected_line = line.replace(orig_prefix, correct_marker, 1)
                issues.append({
                    "original": line,
                    "corrected": corrected_line,
                    "description": f"Malformed command marker or lowercase command name. Should be '{correct_marker.strip()}'.",
                    "type": "syntax",
                    "start_line": i + 1
                })
    return issues