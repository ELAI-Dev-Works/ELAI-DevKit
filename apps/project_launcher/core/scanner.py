from systems.os.platform import is_windows

class ProjectScanner:
    @staticmethod
    def scan(fs):
        launch_files = {'run_bat': None, 'other_bats': [], 'scripts':[]}
        input_requirements = {}
        has_requirements = False
        should_suggest = False

        if not fs.root or not fs.exists(""):
            return launch_files, input_requirements, False

        for item in fs.listdir(""):
            if not fs.exists(item) or fs.is_dir(item): continue

            lower_item = item.lower()
            needs_input = False

            # Always allow input for executable scripts
            if lower_item.endswith(('.py', '.js', '.ts', '.bat', '.ps1', '.cmd', '.c', '.cpp', '.h', '.sh', '.exe')):
                needs_input = True

            input_requirements[item] = needs_input

            if lower_item == 'run.bat' and is_windows():
                launch_files['run_bat'] = item
            elif lower_item == 'run.sh' and not is_windows():
                launch_files['run_bat'] = item
            elif lower_item.endswith('.bat'):
                launch_files['other_bats'].append(item)
            elif lower_item.endswith(('.py', '.html', '.exe', '.js', '.ts', '.sh')):
                launch_files['scripts'].append(item)
            elif lower_item in ('requirements.txt', 'requirements.in', 'package.json'):
                has_requirements = True

        if not launch_files['run_bat'] and not launch_files['other_bats'] and has_requirements:
            should_suggest = True

        return launch_files, input_requirements, should_suggest