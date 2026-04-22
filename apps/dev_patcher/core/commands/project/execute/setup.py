from typing import Tuple, List
from .setup_args import name, run as run_arg, requi, tree, python, nodejs, npm
from .setup_args import all_os, win_os, linux_os, mac_os
from .setup_args import web, server

def run(args: list, content: str, fs_handler) -> Tuple[bool, str]:
    temp_args = list(args)

    # --- 1. Parse all arguments to gather configuration ---
    project_name = name.parse(temp_args)
    launch_file = run_arg.parse(temp_args)
    npm_command = npm.parse(temp_args) # New argument parser
    dependencies_str = requi.parse(temp_args)
    server_type = server.parse(temp_args)
    use_tree = tree.parse(temp_args)

    # Platforms
    use_all_os = all_os.parse(temp_args)
    use_win = win_os.parse(temp_args)
    use_linux = linux_os.parse(temp_args)
    use_mac = mac_os.parse(temp_args)

    # Determine target platforms
    target_platforms = set()
    if use_all_os or use_win:
        target_platforms.add('win')
    if use_all_os or use_linux or use_mac:
        target_platforms.add('unix')

    # Default to all if nothing specified (for backward compatibility/ease of use)
    if not target_platforms:
        target_platforms = {'win', 'unix'}

    # Modes
    use_python = python.parse(temp_args)
    use_nodejs = nodejs.parse(temp_args)
    use_web = web.parse(temp_args)
    
    if not launch_file:
        return False, "The argument -run <file> was not found or was not in the correct format."

    if dependencies_str is None:
        return False, "The argument -requi <dependencies> was not found or was not in the correct format."

    dependencies = []
    if dependencies_str.lower() != 'none':
        dependencies = [dep.strip() for dep in dependencies_str.split('|') if dep.strip()]

    mode = ''
    if use_python:
        mode = 'python'
    elif use_nodejs:
        mode = 'nodejs'
    elif use_web:
        mode = 'web'
    else:
        return False, "Installation mode not specified: -python, -nodejs, or -web."

    # --- 2. Parse content block ---
    structure_content, project_files_content = _parse_main_content(content)

    # --- 3. Execute Actions in Order ---
    try:
        # Create environment files
        if mode == 'python':
            # Python now generates files based on target platforms
            success, msg = python.run(fs_handler, launch_file, dependencies, project_name, target_platforms)
            if not success: return False, msg
        elif mode == 'nodejs':
            # Pass npm_command explicitly and target platforms
            success, msg = nodejs.run(fs_handler, launch_file, dependencies, project_name, npm_command, target_platforms)
            if not success: return False, msg
        
        elif mode == 'web':
            success, msg = web.run(fs_handler, launch_file, dependencies, project_name, server_type, target_platforms)
            if not success: return False, msg
        
    
        # Create default launch file if it doesn't exist.
        # For NodeJS, if we used -npm, launch_file is just 'main' entry, so we still might want to create it if it's a file.
        # Simple check: if launch_file looks like a file (has extension), try to create it.
        if '.' in launch_file and not launch_file.startswith('{'):
            success, msg = run_arg.run(fs_handler, launch_file, project_name)
            if not success: return False, msg

        # Create structure from ---structure--- block
        if use_tree and structure_content:
            success, msg = tree.run(fs_handler, structure_content)
            if not success: return False, f"Error creating structure: {msg}"

        # Create/fill files from ---project--- block
        if project_files_content:
            success, msg = _create_files_from_content(project_files_content, fs_handler)
            if not success: return False, f"Error creating files: {msg}"

        return True, f"Project '{project_name}' has been successfully configured in '{mode}' mode."
    except Exception as e:
        import traceback
        return False, f"Error while setting up project: {e}\n{traceback.format_exc()}"

def _parse_main_content(content: str) -> Tuple[str, str]:
    structure, files = "", ""
    if "---structure---" in content:
        parts = content.split("---structure---", 1)
        if "---project---" in parts[1]:
            sub_parts = parts[1].split("---project---", 1)
            structure = sub_parts[0].strip()
            files = sub_parts[1].strip()
        else:
            structure = parts[1].strip()
    elif "---project---" in content:
        files = content.split("---project---", 1)[1].strip()
    return structure, files

def _create_files_from_content(content: str, fs):
    file_blocks = content.split("<###|")[1:]
    if not file_blocks and content.strip():
        return False, "Block '---project---' is not empty, but no '<###|' separators were found."
    for block in file_blocks:
        if "---file_end---" not in block:
            return False, f"The file block is missing the '---file_end---' marker."
        parts = block.split('\n', 1)
        filepath = parts[0].strip()
        if filepath.endswith('>'):
            filepath = filepath[:-1]
        file_content = parts[1].rsplit("---file_end---", 1)[0].strip('\r\n')
        if not filepath: return False, "A file block with no path specified was found."
        try:
            fs.write(filepath, file_content)
        except Exception as e:
            return False, f"Failed to write file '{filepath}': {e}"
    return True, "Project files have been created successfully."

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    # 1. Python Mode
    content_py = "---project---\n<###| @ROOT/main.py\nprint('hello')\n---file_end---"
    succ, msg = run(['-setup', '-python', '-run', '<main.py>', '-requi', '<requests|colorama>'], content_py, vfs)
    passed = succ and vfs.exists('@ROOT/main.py') and vfs.exists('@ROOT/requirements.in')
    res.append(("Setup Python Project Integration", passed, msg))

    # 2. NodeJS Mode
    content_node = "---project---\n<###| @ROOT/server.js\nconsole.log('hi');\n---file_end---"
    succ, msg = run(['-setup', '-nodejs', '-run', '<server.js>', '-requi', '<express|cors>'], content_node, vfs)
    passed = succ and vfs.exists('@ROOT/server.js') and vfs.exists('@ROOT/package.json')
    res.append(("Setup NodeJS Project Integration", passed, msg))

    # 3. HTML5 Web Mode
    succ, msg = run(['-setup', '-web', '-run', '<index.html>', '-requi', '<src:https://cdn/phaser.js|css:style.css>', '-server', '<Python>'], "", vfs)
    passed = succ and vfs.exists('@ROOT/index.html') and vfs.exists('@ROOT/server.bat')
    res.append(("Setup Web Project Integration", passed, msg))

    return res