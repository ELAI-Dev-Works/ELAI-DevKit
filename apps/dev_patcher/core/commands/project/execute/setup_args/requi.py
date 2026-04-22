def parse(args_list):
    try:
        if '-requi' not in args_list:
            return None

        arg_index = args_list.index('-requi')
        start_index = arg_index + 1

        if start_index >= len(args_list):
            return None

        first_token = args_list[start_index]

        if first_token.startswith('<'):
            parts =[]
            end_index = -1
            for i in range(start_index, len(args_list)):
                token = args_list[i]
                parts.append(token)
                if token.endswith('>'):
                    end_index = i
                    break

            if end_index != -1:
                for _ in range(start_index, end_index + 1):
                    args_list.pop(start_index)
                args_list.pop(arg_index)
                full_str = " ".join(parts)
                return full_str[1:-1]

    except (ValueError, IndexError):
        pass
    return None

from typing import List, Tuple

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    parsed_py = parse(['-requi', '<pygame|requests>'])
    res.append(("Parse Requi Python", parsed_py == 'pygame|requests', str(parsed_py)))

    parsed_node = parse(['-requi', '<express|cors>'])
    res.append(("Parse Requi NodeJS", parsed_node == 'express|cors', str(parsed_node)))

    parsed_web = parse(['-requi', '<src:https://cdn.jsdelivr.net/npm/phaser.js|css:style.css>'])
    res.append(("Parse Requi Web", parsed_web == 'src:https://cdn.jsdelivr.net/npm/phaser.js|css:style.css', str(parsed_web)))

    parsed_none = parse(['-requi', '<None>'])
    res.append(("Parse Requi None", parsed_none == 'None', str(parsed_none)))
    return res