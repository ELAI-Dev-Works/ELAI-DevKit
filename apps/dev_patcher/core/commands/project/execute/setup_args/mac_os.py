from typing import List, Tuple

def parse(args_list: list) -> bool:
    if '-mac_os' in args_list:
        return True
    return False

def tests(vfs) -> List[Tuple[str, bool, str]]:
    return [("Parse Mac OS", parse(['-mac_os']), "")]