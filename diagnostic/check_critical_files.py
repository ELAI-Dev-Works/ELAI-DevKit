#!/usr/bin/env python3
"""
Diagnostic Script: Critical File Integrity Checker
---------------------------------------------------
Verifies that essential application files exist and are non-empty.
"""
import os
import sys

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

CRITICAL_FILES = [
    "version.txt",
    "launch.py",
    "requirements.txt",
    "requirements.in",
    "core/app.py",
    "core/gui/main.py",
    "core/gui/launch.py",
    "systems/language/manager.py",
    "systems/extension/manager.py",
    "systems/fs/vfs_core.py",
    "apps/dev_patcher/app.py",
    "apps/dev_patcher/core/parser.py",
    "assets/icons/ELAI-DevKit_logo.svg",
]

def main():
    print("========================================")
    print("    Critical File Integrity Checker")
    print("========================================")
    issues = 0
    for f in CRITICAL_FILES:
        path = os.path.join(ROOT_PATH, f)
        if not os.path.exists(path):
            print(f"[FAIL] Missing: {f}")
            issues += 1
        elif os.path.getsize(path) == 0:
            print(f"[FAIL] Empty: {f}")
            issues += 1
        else:
            print(f"[PASS] {f}")
    
    if issues:
        sys.exit(1)
    else:
        print("[PASS] All critical files present.")
        sys.exit(0)

if __name__ == '__main__':
    main()