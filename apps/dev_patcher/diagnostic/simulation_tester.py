import os
import sys
import tempfile
import shutil

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from apps.dev_patcher.core.patch_checking import plan_dynamic_patch

class MockLang:
    def get(self, key, **kwargs): return key

def test_dynamic_patch_planning():
    temp_dir = tempfile.mkdtemp(prefix="elai_sim_test_")
    try:
        # Create dummy project
        os.makedirs(os.path.join(temp_dir, 'src'))
        with open(os.path.join(temp_dir, 'src', 'main.py'), 'w') as f:
            f.write("def start():\n    pass")

        commands = [
            ("MANAGE", ["-create", "@ROOT/config.json"], "{}"),
            ("EDIT", ["-v2", "-replace", "@ROOT/src/main.py"], "---old---\n    pass\n---new---\n    print('started')"),
        ]

        # Run generator
        generator = plan_dynamic_patch(commands, temp_dir, experimental_flags={"enabled": True}, ignore_dirs=[], lang=MockLang())
        results = list(generator)
        
        # Find the final result tuple
        final_result = next((item[1] for item in results if isinstance(item, tuple) and item[0] == 'finished'), None)
        
        assert final_result is not None, "Simulation did not yield a 'finished' state."
        assert len(final_result['plan']) == 2, f"Expected 2 commands in plan, got {len(final_result['plan'])}"
        assert len(final_result['skipped']) == 0, "Expected 0 skipped commands."
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def run_tests():
    tests =[
        ("Dynamic Patch Planning", test_dynamic_patch_planning)
    ]

    passed = 0
    print("Starting DevPatcher Simulation Tests...")
    for name, test_func in tests:
        try:
            test_func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            import traceback
            print(f"  [FAIL] {name}: {e}")
            traceback.print_exc()

    print(f"\\nSimulation Tests Summary: {passed}/{len(tests)} passed.")
    if passed != len(tests):
        sys.exit(1)

if __name__ == '__main__':
    run_tests()