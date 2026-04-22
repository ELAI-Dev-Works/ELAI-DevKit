def parse(args_list):
    try:
        if '-server' not in args_list:
            return None

        arg_index = args_list.index('-server')
        start_index = arg_index + 1

        if start_index >= len(args_list):
            return None

        val = args_list[start_index]
        if val.startswith('<') and val.endswith('>'):
            # Remove the argument and its value from the list
            args_list.pop(start_index)
            args_list.pop(arg_index)
            return val[1:-1] # Return content without brackets
    except (ValueError, IndexError):
        pass
    return None

from typing import List, Tuple

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    parsed = parse(['-server', '<Python>'])
    res.append(("Parse Server", parsed == 'Python', str(parsed)))
    return res
