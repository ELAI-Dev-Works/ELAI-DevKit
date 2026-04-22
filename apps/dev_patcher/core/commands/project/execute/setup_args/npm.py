def parse(args_list: list):
    """
    Parses the -npm argument.
    Supports simple format: -npm <{command}>
    Supports advanced format: -npm <run:{cmd}|scripts/start:{cmd}|...>
    Returns either a string (simple) or a dict (advanced).
    """
    try:
        if '-npm' not in args_list:
            return None

        arg_index = args_list.index('-npm')
        start_index = arg_index + 1

        if start_index >= len(args_list):
            return None

        first_token = args_list[start_index]

        if first_token.startswith('<'):
            parts =[]
            end_index = -1

            # Gather tokens until one ends with '>'
            for i in range(start_index, len(args_list)):
                token = args_list[i]
                parts.append(token)
                if token.endswith('>'):
                    end_index = i
                    break

            if end_index != -1:
                # Remove used tokens
                for _ in range(start_index, end_index + 1):
                    args_list.pop(start_index)
                args_list.pop(arg_index) # Remove -npm argument

                full_str = " ".join(parts)
                content = full_str[1:-1].strip() # Remove < and >

                # --- Advanced Parsing Logic ---
                # Check if it contains pipe separator or explicit keys
                if '|' in content or content.startswith('run:') or content.startswith('scripts/'):
                    result = {'run': None, 'scripts': {}}
                    segments = content.split('|')
                    for seg in segments:
                        if ':' in seg:
                            key, val = seg.split(':', 1)
                            key = key.strip()
                            val = val.strip()
                            # Clean wrapping braces { }
                            if val.startswith('{') and val.endswith('}'):
                                val = val[1:-1].strip()

                            if key == 'run':
                                result['run'] = val
                            elif key.startswith('scripts/'):
                                script_name = key.split('/', 1)[1]
                                result['scripts'][script_name] = val
                    return result

                # --- Legacy Simple Logic ---
                if content.startswith('{') and content.endswith('}'):
                    return content[1:-1].strip()

                return content.strip()

    except (ValueError, IndexError):
        pass
    return None

from typing import List, Tuple

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res = []
    args =['-npm', '<run:{npm start}|scripts/test:{jest}>']
    parsed = parse(args)
    passed = parsed is not None and parsed.get('run') == 'npm start'
    res.append(("NPM Parse Advanced", passed, str(parsed)))
    return res