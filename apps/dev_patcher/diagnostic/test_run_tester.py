import os
import sys
import tempfile
import shutil

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from apps.dev_patcher.core.test_run.runner import TestRunner
from apps.dev_patcher.core.test_run.architectures import get_architecture
from systems.fs.vfs_core import AdvancedVFS

def test_runner_preparation():
    proj_dir = tempfile.mkdtemp(prefix="elai_runner_proj_")
    try:
        with open(os.path.join(proj_dir, "script.py"), "w") as f:
            f.write("print('original')")

        vfs = AdvancedVFS(proj_dir)
        vfs.mount()

        vfs.write("script.py", "print('modified')")
        vfs.write("new_file.txt", "new")
        
        runner = TestRunner(vfs, proj_dir, None)
        temp_env = runner.prepare()
        
        assert os.path.exists(temp_env), "Sandbox temp directory was not created."
        
        # Check if modified file is present
        with open(os.path.join(temp_env, "script.py"), "r") as f:
            assert f.read() == "print('modified')", "Modified content was not copied to sandbox."
            
        # Check if new file is present
        with open(os.path.join(temp_env, "new_file.txt"), "r") as f:
            assert f.read() == "new", "New file was not created in sandbox."
            
        # Check architecture generation
        arch = get_architecture(temp_env, proj_dir, "script.py")
        cmd = arch.get_launch_command()
        
        
        runner.cleanup()
        assert not os.path.exists(temp_env), "Sandbox temp directory was not cleaned up."
        
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)

def run_tests():
    tests =[
        ("TestRunner Sandbox Prep & Architecture", test_runner_preparation)
    ]

    passed = 0
    print("Starting DevPatcher TestRun Tests...")
    for name, test_func in tests:
        try:
            test_func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            import traceback
            print(f"  [FAIL] {name}: {e}")
            traceback.print_exc()

    print(f"\\nTestRun Tests Summary: {passed}/{len(tests)} passed.")
    if passed != len(tests):
        sys.exit(1)

if __name__ == '__main__':
    run_tests()