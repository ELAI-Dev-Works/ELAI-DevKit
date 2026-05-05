#!/usr/bin/env python3
"""
Diagnostic Script: Asset Integrity Checker
-------------------------------------------
Validates that all extensions have a valid metadata.json and that
all icon references exist as SVG files in the correct directories.
"""
import os
import sys
import json
import re

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def check_metadata(apps_dir, ext_type):
    issues = []
    if not os.path.isdir(apps_dir):
        return issues
    for ext_name in os.listdir(apps_dir):
        ext_path = os.path.join(apps_dir, ext_name)
        if not os.path.isdir(ext_path):
            continue
        meta_path = os.path.join(ext_path, "metadata.json")
        if not os.path.exists(meta_path):
            issues.append(f"[{ext_type}] {ext_name}: Missing metadata.json")
            continue
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            required = ["name", "version", "description"]
            for field in required:
                if field not in meta:
                    issues.append(f"[{ext_type}] {ext_name}: metadata.json missing '{field}'")
        except Exception as e:
            issues.append(f"[{ext_type}] {ext_name}: Invalid metadata.json ({e})")
    return issues

def check_icons(apps_dir, core_icons_path):
    issues = []
    used_icons = set()
    icon_ref_re = re.compile(r'\.get_icon\(\s*["\'](core\.[a-zA-Z0-9_]+)["\']\)')
    icon_ref_q = re.compile(r'IconManager\.get_icon\(\s*["\']([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)["\']\)')
    # Scan Python files for icon references
    for root, _, files in os.walk(os.path.join(ROOT_PATH, "apps", "dev_patcher")):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for match in icon_ref_re.findall(content):
                        used_icons.add(match)
                    for match in icon_ref_q.findall(content):
                        used_icons.add(match)
    # Check existence
    for ref in used_icons:
        uid, icon_name = ref.split('.')
        found = False
        if uid == 'core':
            path = os.path.join(ROOT_PATH, "assets", "icons", f"{icon_name}.svg")
            found = os.path.exists(path)
        else:
            # Check in apps/*/assets/icons/ and extensions/custom_apps/*/assets/icons/
            for base in [os.path.join(ROOT_PATH, "apps", uid), os.path.join(ROOT_PATH, "extensions", "custom_apps", uid)]:
                path = os.path.join(base, "assets", "icons", f"{icon_name}.svg")
                if os.path.exists(path):
                    found = True
                    break
        if not found:
            issues.append(f"Icon not found: '{ref}' (resolved to {path if 'path' in locals() else 'unknown'})")
    return issues

def main():
    print("========================================")
    print("         Asset Integrity Checker")
    print("========================================")
    issues = []
    issues.extend(check_metadata(os.path.join(ROOT_PATH, "apps"), "Core App"))
    issues.extend(check_metadata(os.path.join(ROOT_PATH, "extensions", "custom_apps"), "Extension"))
    issues.extend(check_icons(os.path.join(ROOT_PATH, "apps"), None))
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}")
        sys.exit(1)
    else:
        print("[PASS] All assets are valid.")
        sys.exit(0)

if __name__ == '__main__':
    main()