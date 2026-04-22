from typing import Tuple

def parse(args_list: list) -> str:
    try:
        if '-run' not in args_list:
            return None

        arg_index = args_list.index('-run')
        start_index = arg_index + 1

        if start_index >= len(args_list):
            return None

        first_token = args_list[start_index]

        # Case 1: Single token <main.py>
        if first_token.startswith('<') and first_token.endswith('>'):
            args_list.pop(start_index)
            args_list.pop(arg_index)
            return first_token[1:-1]

        # Case 2: Multi-token <npm run dev>
        if first_token.startswith('<'):
            parts = []
            end_index = -1
            # Gather tokens until one ends with '>'
            for i in range(start_index, len(args_list)):
                token = args_list[i]
                parts.append(token)
                if token.endswith('>'):
                    end_index = i
                    break

            if end_index != -1:
                # Remove used tokens (reverse order to keep indices valid)
                for _ in range(start_index, end_index + 1):
                    args_list.pop(start_index)
                args_list.pop(arg_index) # Remove -run argument itself

                full_str = " ".join(parts)
                return full_str[1:-1] # Remove < and >

    except (ValueError, IndexError):
        pass
    return None

def run(fs, launch_file: str, project_name: str) -> Tuple[bool, str]:
    if not fs.exists(f"@ROOT/{launch_file}"):
        try:
            launch_content = (
                f'# {launch_file}\n\n'
                'import sys\n\n'
                'def main():\n'
                f'    print("Hello from {project_name}!")\n'
                # Use double braces to escape them in f-string, so they appear in the final file
                '    print(f"Arguments: {sys.argv}")\n\n'
                'if __name__ == "__main__":\n'
                '    main()\n'
            )
            fs.write(f"@ROOT/{launch_file}", launch_content)
            return True, f"A default startup file has been created: {launch_file}"
        except Exception as e:
            return False, f"Failed to create startup file: {e}"
    return True, "The launch file already exists."

from typing import List, Tuple

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res = []
    parsed = parse(['-run', '<main.py>'])
    res.append(("Parse Run", parsed == 'main.py', str(parsed)))

    succ, msg = run(vfs, 'main.py', 'TestProj')
    passed = succ and vfs.exists('@ROOT/main.py')
    res.append(("Run File Create", passed, msg))
    return res
