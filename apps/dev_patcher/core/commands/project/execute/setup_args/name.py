def parse(args_list):
    """
    Parses the -name argument.
    Formats:
    -name <My_Project> (No spaces)
    -name <(My Project Name)> (With spaces, requires parenthesis inside brackets)
    """
    try:
        if '-name' not in args_list:
            return "Project Launcher"

        arg_index = args_list.index('-name')
        start_index = arg_index + 1

        if start_index >= len(args_list):
            return "Project Launcher"

        first_token = args_list[start_index]

        parts = []
        end_index = -1

        # Start gathering tokens
        for i in range(start_index, len(args_list)):
            token = args_list[i]
            parts.append(token)
            if token.endswith('>'):
                end_index = i
                break
        
        if end_index != -1:
            # Remove tokens from list
            for _ in range(start_index, end_index + 1):
                args_list.pop(start_index)
            args_list.pop(arg_index)

            full_str = " ".join(parts)
            content = full_str[1:-1] # Remove < and >

            # Check for parenthesis wrapper for spaced names
            if content.startswith('(') and content.endswith(')'):
                return content[1:-1].strip()
            
            return content.strip()

    except (ValueError, IndexError):
        pass
    return "Project Launcher"

from typing import List, Tuple

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res = []
    parsed = parse(['-name', '<(My Test Project)>'])
    res.append(("Parse Name with spaces", parsed == 'My Test Project', str(parsed)))
    return res
