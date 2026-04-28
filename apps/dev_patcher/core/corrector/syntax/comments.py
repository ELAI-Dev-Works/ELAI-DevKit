import re

def check_comments_syntax(lines, lang):
    issues =[]
    for i, line in enumerate(lines):
        match_start = re.search(r"<\s*-\s*@", line)
        if match_start and match_start.group() != "<-@":
            corrected = line.replace(match_start.group(), "<-@", 1)
            issues.append({
                "original": line, "corrected": corrected,
                "description": "Malformed single-line comment start marker. Should be '<-@'.",
                "type": "syntax", "start_line": i + 1
            })
        
        match_end = re.search(r"@\s*-\s*>", line)
        if match_end and match_end.group() != "@->":
            corrected = line.replace(match_end.group(), "@->", 1)
            issues.append({
                "original": line, "corrected": corrected,
                "description": "Malformed single-line comment end marker. Should be '@->'.",
                "type": "syntax", "start_line": i + 1
            })

        match_multi = re.search(r"#\s*@\s*#", line)
        if match_multi and match_multi.group() != "#@#":
            corrected = line.replace(match_multi.group(), "#@#", 1)
            issues.append({
                "original": line, "corrected": corrected,
                "description": "Malformed multi-line comment marker. Should be '#@#'.",
                "type": "syntax", "start_line": i + 1
            })
    return issues