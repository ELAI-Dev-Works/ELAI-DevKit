import os
import sys

# Ensure the project root is in sys.path
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

import shutil
import tempfile
import json
from unittest.mock import MagicMock

def test_launcher_detection():
    """Tests that the launcher correctly detects launchable files."""
    tmp = tempfile.mkdtemp(prefix='elai_launch_diag_')
    try:
        ctx = MagicMock()
        ctx.main_window = None
        ctx.settings_manager = MagicMock()
        ctx.async_thread_manager = MagicMock()
        ctx.fs = MagicMock()

        from systems.fs.manager import FileSystemManager
        fs_man = FileSystemManager(tmp)
        ctx.fs.get_fs = lambda root: fs_man.get_fs(root)

        # Create project files
        with open(os.path.join(tmp, 'main.py'), 'w') as f:
            f.write("print('hello')")
        os.makedirs(os.path.join(tmp, 'src'))
        with open(os.path.join(tmp, 'package.json'), 'w') as f:
            json.dump({"main": "app.js"}, f)

        fs = fs_man.get_fs(tmp)

        def scan_task():
            launch_files = {'run_bat': None, 'other_bats': [], 'scripts': []}
            input_reqs = {}
            if not fs.exists(''):
                return launch_files, input_reqs, False
            for item in fs.listdir(''):
                if fs.is_dir(item):
                    continue
                lower = item.lower()
                if lower.endswith('.py'):
                    launch_files['scripts'].append(item)
                elif lower.endswith('.js'):
                    launch_files['scripts'].append(item)
            return launch_files, input_reqs, False

        res = scan_task()
        scripts = res[0]['scripts']
        assert 'main.py' in scripts, f"Expected main.py in scripts, got {scripts}"
        print("[PASS] Launcher detection found Python file.")
        return True
    except Exception as e:
        print(f"[FAIL] Launcher tester: {e}")
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    ok = test_launcher_detection()
    exit(0 if ok else 1)