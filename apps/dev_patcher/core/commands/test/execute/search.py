import os
from typing import Tuple
from typing import List

def run(args: list, content: str, fs) -> Tuple[bool, str]:
    ignore_list = set()

    search_arg = next((a for a in args if a.startswith('<') and a.endswith('>')), None)
    if not search_arg:
        return False, "No keywords in the format <keywords> were specified for the search."

    search_keywords_str = search_arg[1:-1]
    keywords = search_keywords_str.split('|')

    if "-ignore" in args:
        try:
            ignore_index = args.index("-ignore")
            ignore_arg = args[ignore_index + 1]
            if ignore_arg.startswith('<') and ignore_arg.endswith('>'):
                ignore_patterns_str = ignore_arg[1:-1]
                ignore_list = set(ignore_patterns_str.split('|'))
            else:
                return False, "Ignore patterns must be in the format <-ignore <pattern1|pattern2>>"
        except IndexError:
            return False, "Incorrect use of -ignore."

    matches = []
    for dirpath, dirnames, filenames in fs.walk(fs.root):
        dirnames[:] = [d for d in dirnames if d not in ignore_list]

        for item in dirnames + filenames:
            for keyword in keywords:
                if keyword.lower() in item.lower():
                    full_item_path = os.path.join(dirpath, item)
                    rel_path = os.path.relpath(full_item_path, fs.root)
                    matches.append(rel_path.replace('\\', '/'))
                    break

    if not matches:
        return True, "Search completed. Nothing found."
    return True, "Search results:\n" + "\n".join(sorted(list(set(matches))))

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res = []
    # Setup files
    vfs.write('@ROOT/src/api_handler.py', 'data')
    vfs.makedirs('@ROOT/.venv/api_cache') # A folder containing the keyword
    vfs.write('@ROOT/.venv/lib/some_api_lib.py', 'data') # A file containing the keyword

    # Test 1: Search without ignore
    succ, msg = run(['-search', '<api>'], '', vfs)
    passed = (succ and
              'src/api_handler.py' in msg and
              '.venv/api_cache' in msg and
              '.venv/lib/some_api_lib.py' in msg)
    res.append(("Search Keyword", passed, msg))

    # Test 2: Search with ignore
    succ, msg = run(['-search', '<api>', '-ignore', '<.venv>'], '', vfs)
    passed = (succ and
              'src/api_handler.py' in msg and
              '.venv' not in msg) # The crucial check
    res.append(("Search with Ignore", passed, msg))

    return res