import re

def check_raw_blocks_syntax(lines, lang):
    issues =[]
    for i, line in enumerate(lines):
        match_run = re.search(r"\{\s*!\s*RUN\s*\}", line, re.IGNORECASE)
        if match_run and match_run.group() != "{!RUN}":
            corrected = line.replace(match_run.group(), "{!RUN}", 1)
            issues.append({
                "original": line, "corrected": corrected,
                "description": "Malformed raw execution start tag. Should be '{!RUN}'.",
                "type": "syntax", "start_line": i + 1
            })

        match_end = re.search(r"\{\s*!\s*END\s*\}", line, re.IGNORECASE)
        if match_end and match_end.group() != "{!END}":
            corrected = line.replace(match_end.group(), "{!END}", 1)
            issues.append({
                "original": line, "corrected": corrected,
                "description": "Malformed raw execution end tag. Should be '{!END}'.",
                "type": "syntax", "start_line": i + 1
            })
    return issues