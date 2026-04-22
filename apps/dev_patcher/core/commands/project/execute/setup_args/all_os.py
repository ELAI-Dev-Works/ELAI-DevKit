from typing import List, Tuple

def parse(args_list: list) -> bool:
    if '-all_os' in args_list:
        return True
    return False

def tests(vfs) -> List[Tuple[str, bool, str]]:
    return[("Parse All OS", parse(['-all_os']), "")]