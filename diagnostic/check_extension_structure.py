#!/usr/bin/env python3
"""
Diagnostic Script: Extension Structure Validator
Checks that all extensions (apps and custom) have valid structure and required files.
"""
import os
import sys
import json

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def check_extensions(apps_dir, ext_type):
    issues = []
    if not os.path.isdir(apps_dir):
        return issues
    for ext_name in os.listdir(apps_dir):
        ext_path = os.path.join(apps_dir, ext_name)
        if not os.path.isdir(ext_path):
            continue
        # Check app.py
        if not os.path.exists(os.path.join(ext_path, "app.py")):
            issues.append(f"[{ext_type}] {ext_name}: Missing app.py")
        # Check metadata.json
        meta_path = os.path.join(ext_path, "metadata.json")
        if not os.path.exists(meta_path):
            issues.append(f"[{ext_type}] {ext_name}: Missing metadata.json")
        else:
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                # check key fields
                if 'name' not in meta:
                    issues.append(f"[{ext_type}] {ext_name}: metadata.json missing 'name'")
            except Exception as e:
                issues.append(f"[{ext_type}] {ext_name}: Invalid metadata.json ({e})")
        # Check structure version consistency
        if os.path.exists(os.path.join(ext_path, "gui", "windows", "core.py")):
            # V2 extension should NOT have app_gui.py (old V1)
            if os.path.exists(os.path.join(ext_path, "app_gui.py")):
                issues.append(f"[{ext_type}] {ext_name}: Detected V2 structure but obsolete app_gui.py exists.")
        else:
            # V1 extension must have app_gui.py
            if not os.path.exists(os.path.join(ext_path, "app_gui.py")):
                issues.append(f"[{ext_type}] {ext_name}: Missing app_gui.py (V1 extension).")
    return issues

def main():
    print("=" * 50)
    print("    Extension Structure Validator")
    print("=" * 50)
    all_issues = []
    all_issues.extend(check_extensions(os.path.join(ROOT_PATH, "apps"), "Core App"))
    all_issues.extend(check_extensions(os.path.join(ROOT_PATH, "extensions", "custom_apps"), "Extension"))
    if all_issues:
        for issue in all_issues:
            print(f"[FAIL] {issue}")
        sys.exit(1)
    else:
        print("[PASS] All extension structures are valid.")
        sys.exit(0)

if __name__ == '__main__':
    main()