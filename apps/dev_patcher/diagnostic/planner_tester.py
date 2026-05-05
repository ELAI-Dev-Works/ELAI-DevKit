#!/usr/bin/env python3
"""
Diagnostic Script: Command Planner Tester
-------------------------------------------
Verifies that the command execution planner correctly sorts commands
by priority, respecting the documented execution order.
"""
import os
import sys

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

from apps.dev_patcher.core.command_planner import plan_execution_order

def test_plan_order():
    commands = [
        ("EDIT", ["-v2", "-replace", "@ROOT/file.py"], "---old---\nx=1\n---new---\nx=2"),
        ("TEST", ["-print"], "Hello"),
        ("PROJECT", ["-setup", "-python", "-run", "<main.py>", "-requi", "<None>"], ""),
        ("MANAGE", ["-create", "@ROOT/config.json"], "{}"),
    ]
    ordered = plan_execution_order(commands, project_root=None)
    names = [cmd[0] for cmd in ordered]
    # Expected order: TEST (0), PROJECT (1), ..., MANAGE (4), EDIT (5)
    assert names == ["TEST", "PROJECT", "MANAGE", "EDIT"], f"Got {names}"
    print("  [PASS] Commands sorted by priority.")

def test_custom_command_fallback():
    # If a command is not a standard one, it gets default priority 99 (appears last)
    commands = [
        ("UNKNOWN", [], ""),
        ("EDIT", ["-v2", "-replace", "@ROOT/x.py"], ""),
    ]
    ordered = plan_execution_order(commands, project_root=None)
    # EDIT (priority 5) should come before UNKNOWN (priority 99)
    assert ordered[0][0] == "EDIT"
    assert ordered[1][0] == "UNKNOWN"
    print("  [PASS] Unknown commands go last.")

def run_tests():
    tests = [
        ("Planner: Correct Priority Order", test_plan_order),
        ("Planner: Unknown Command Fallback", test_custom_command_fallback),
    ]
    passed = 0
    for name, func in tests:
        try:
            func()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")

    print(f"\nPlanner Tester Summary: {passed}/{len(tests)} passed.")
    if passed != len(tests):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    run_tests()