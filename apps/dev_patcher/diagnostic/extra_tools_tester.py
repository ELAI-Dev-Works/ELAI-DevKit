#!/usr/bin/env python3
"""
Diagnostic Script: Extra Patcher Tools Tester
-----------------------------------------------
Validates fuzzy matching, scope matching, and precise patching logic
by exercising the underlying standalone functions.
"""
import os
import sys

# Ensure project root is in sys.path
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

from apps.dev_patcher.core.patcher_tools.extra.fuzzy_matching import find_best_match
from apps.dev_patcher.core.patcher_tools.extra.scope_matching import find_scope_boundaries
from apps.dev_patcher.core.parser import _strip_line_number

def test_fuzzy_matching():
    source = [
        "def hello_world():",
        "    print('Hello')",
        "    print('World')",
    ]
    target = "def hello_world():\n    print('Hello')"
    idx, ratio = find_best_match(source, target, threshold=0.85)
    assert idx == 0, f"Expected index 0, got {idx}"
    assert ratio >= 0.85, f"Expected ratio >=0.85, got {ratio}"
    print("  [PASS] Fuzzy matching found exact match.")

    # Test near miss
    source_modified = [
        "def hello_world():",
        "    print('Hello there')",
        "    print('World')",
    ]
    idx, ratio = find_best_match(source_modified, target, threshold=0.7)
    assert idx == 0, f"Expected near match at 0, got {idx}"
    assert ratio >= 0.7, "Expected ratio >=0.7 for similar code"
    print("  [PASS] Fuzzy matching found near match.")

def test_scope_matching():
    original = [
        "class App:",
        "    def run(self):",
        "        pass",
        "    def stop(self):",
        "        pass",
    ]
    scope_block = "class App:"
    start, end, ratio = find_scope_boundaries(original, scope_block, threshold=0.8)
    assert start == 0
    # End should be the end of the class block (4 lines)
    assert end == len(original), f"Expected end {len(original)}, got {end}"
    print("  [PASS] Scope matching found class boundaries.")

def test_precise_patching_stripping():
    cleaned = _strip_line_number("  12| x = 1")
    assert cleaned == "x = 1", f"Expected 'x = 1', got '{cleaned}'"
    cleaned2 = _strip_line_number(" x = 2")
    assert cleaned2 == " x = 2", f"Untouched line should remain, got '{cleaned2}'"
    print("  [PASS] Line number stripping works correctly.")

def run_tests():
    tests = [
        ("Extra Tools: Fuzzy Matching", test_fuzzy_matching),
        ("Extra Tools: Scope Matching", test_scope_matching),
        ("Extra Tools: Precise Patching Stripping", test_precise_patching_stripping),
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

    print(f"\nExtra Tools Tester Summary: {passed}/{len(tests)} passed.")
    if passed != len(tests):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    run_tests()