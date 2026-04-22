def generate_error_block(content: str, error_message: str, line_number: int = None) -> str:
    """
    Generates a formatted error block containing the original error message
    and a snippet of code around the error line.
    """
    if not line_number or line_number < 1 or not content:
        return f"{error_message}\n\n[Code Context Unavailable]"

    lines = content.splitlines()
    total_lines = len(lines)
    
    start_line = max(1, line_number - 3)
    end_line = min(total_lines, line_number + 3)
    
    snippet = []
    snippet.append(f"{error_message}")
    snippet.append("-" * 60)
    
    for i in range(start_line, end_line + 1):
        idx = i - 1
        line_text = lines[idx] if idx < total_lines else ""
        
        prefix = "-> " if i == line_number else "   "
        snippet.append(f"{prefix}{i:4d} | {line_text}")
        
    snippet.append("-" * 60)
    
    return "\n".join(snippet)