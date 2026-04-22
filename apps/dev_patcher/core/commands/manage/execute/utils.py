from typing import List, Tuple

def reconstruct_paths(args: List[str]) -> List[str]:
    """
    Reconstructs arguments that were split by spaces inside quotes.
    Example:['-move', '"path/to', 'my', 'file"'] ->['-move', 'path/to my file']
    """
    new_args =[]
    i = 0
    while i < len(args):
        arg = args[i]
        # Case 1: Start of a multi-word quoted path (starts with ", but doesn't end with one)
        if arg.startswith('"') and not (len(arg) > 1 and arg.endswith('"')):
            reconstructed_path_parts = [arg[1:]]  # Remove starting quote
            i += 1
            # Consume subsequent parts until one ends with a quote
            while i < len(args):
                part = args[i]
                if part.endswith('"'):
                    reconstructed_path_parts.append(part[:-1])  # Remove ending quote and append
                    i += 1
                    break
                else:
                    reconstructed_path_parts.append(part)
                    i += 1
            new_args.append(" ".join(reconstructed_path_parts))
        # Case 2: A single, self-contained quoted path
        elif arg.startswith('"') and arg.endswith('"'):
            new_args.append(arg[1:-1])
            i += 1
        # Case 3: A normal, unquoted argument
        else:
            new_args.append(arg)
            i += 1
    return new_args

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res = []
    parsed = reconstruct_paths(['-move', '"my', 'folder/file.txt"', 'to', 'dest'])
    passed = parsed == ['-move', 'my folder/file.txt', 'to', 'dest']
    res.append(("Reconstruct Quoted Paths", passed, str(parsed)))
    return res