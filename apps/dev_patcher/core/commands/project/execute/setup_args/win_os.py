from typing import List, Tuple

def parse(args_list: list) -> bool:
    if '-win_os' in args_list:
        return True
    return False

def tests(vfs) -> List[Tuple[str, bool, str]]:
    return[("Parse Win OS", parse(['-win_os']), "")]