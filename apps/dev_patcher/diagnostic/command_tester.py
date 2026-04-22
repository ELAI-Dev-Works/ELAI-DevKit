import os
import sys
import importlib.util
import traceback

def run_command_tests():
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if root_path not in sys.path:
        sys.path.insert(0, root_path)

    from apps.dev_patcher.core.fs_handler import VirtualFileSystem

    search_dirs =[
        os.path.join(root_path, 'apps', 'dev_patcher', 'core', 'commands'),
        os.path.join(root_path, 'extensions', 'custom_commands')
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests =[]

    print("Starting DevPatcher Command Unit Tests...")

    for s_dir in search_dirs:
        if not os.path.exists(s_dir): continue
        for root, _, files in os.walk(s_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_path)
                    mod_name = rel_path[:-3].replace(os.sep, '.')
                    try:
                        mod = importlib.import_module(mod_name)

                        if hasattr(mod, 'tests'):
                            vfs = VirtualFileSystem(root_path)
                            results = mod.tests(vfs)
                            for name, success, msg in results:
                                total_tests += 1
                                if success:
                                    passed_tests += 1
                                    print(f"  [PASS] {file} -> {name}")
                                else:
                                    failed_tests.append(f"{file} -> {name}: {msg}")
                                    print(f"  [FAIL] {file} -> {name}")
                    except Exception as e:
                        print(f"  [ERROR] Failed to load or run tests in {file}: {e}")
                        failed_tests.append(f"{file} -> Load Error: {e}")

    print(f"\\nCommand Tests Summary: {passed_tests}/{total_tests} passed.")
    if failed_tests:
        print("\\nFailed Tests:")
        for fail in failed_tests:
            print(f"  - {fail}")
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    run_command_tests()