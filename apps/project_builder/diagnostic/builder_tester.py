import os
import sys

# Ensure the project root is in sys.path
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

import shutil
import tempfile
import json
from apps.project_builder.core.detector import ProjectDetector
from systems.fs.real_fs import RealFileSystem

def test_builder_detection():
    """Tests that ProjectDetector correctly identifies Python/NodeJS/Web architectures."""
    tmp = tempfile.mkdtemp(prefix='elai_builder_diag_')
    try:
        # Python project
        py_dir = os.path.join(tmp, 'py_proj')
        os.makedirs(py_dir)
        with open(os.path.join(py_dir, 'main.py'), 'w') as f:
            f.write('pass')
        fs_py = RealFileSystem(py_dir)
        det = ProjectDetector.detect(fs_py)
        assert det['architecture'] == 'python', f"Expected python, got {det['architecture']}"
        assert 'main.py' in det['main_files']

        # NodeJS project
        node_dir = os.path.join(tmp, 'node_proj')
        os.makedirs(node_dir)
        with open(os.path.join(node_dir, 'package.json'), 'w') as f:
            json.dump({"main": "index.js"}, f)
        with open(os.path.join(node_dir, 'index.js'), 'w') as f:
            f.write('')
        fs_node = RealFileSystem(node_dir)
        det = ProjectDetector.detect(fs_node)
        assert det['architecture'] == 'nodejs'

        # Web project
        web_dir = os.path.join(tmp, 'web_proj')
        os.makedirs(web_dir)
        with open(os.path.join(web_dir, 'index.html'), 'w') as f:
            f.write('<html></html>')
        fs_web = RealFileSystem(web_dir)
        det = ProjectDetector.detect(fs_web)
        assert det['architecture'] == 'web'

        print("[PASS] Builder detection works for all architectures.")
        return True
    except Exception as e:
        print(f"[FAIL] Builder tester: {e}")
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    ok = test_builder_detection()
    exit(0 if ok else 1)