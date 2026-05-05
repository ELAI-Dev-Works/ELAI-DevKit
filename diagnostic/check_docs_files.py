#!/usr/bin/env python3
"""
Diagnostic Script: Enhanced Documentation File Validator
----------------------------------------------------------
Validates all .cdoc, .csdoc, and .exdoc files across the project.
Checks required metadata, valid types, and structural consistency
with the documentation builder logic.
"""

import os
import sys
import re
from collections import defaultdict

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Valid patterns for the 'type' field
VALID_CDOC_TYPES = {
    "command(base)",
    "command(init)",
    "argument",
    "modifier",
    "sub-argument",
}

def parse_meta(file_path):
    """Extract metadata key-value pairs from a doc file."""
    meta = {}
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#') and not line.startswith('<'):
                key, _, value = line.partition('=')
                meta[key.strip()] = value.strip()
    return meta

def validate_file(file_path, rel_path):
    """Validate a single documentation file. Returns a list of issue strings."""
    issues = []
    meta = parse_meta(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    fname = os.path.basename(file_path)

    # ---- .cdoc ----
    if ext == '.cdoc':
        # Must have 'type'
        if 'type' not in meta:
            issues.append(f"{rel_path}: missing 'type' field")
        else:
            t = meta['type']
            if t not in VALID_CDOC_TYPES:
                issues.append(f"{rel_path}: invalid type '{t}' (expected one of {VALID_CDOC_TYPES})")

        # Must have 'number' (integer or '#')
        if 'number' not in meta:
            issues.append(f"{rel_path}: missing 'number' field")
        else:
            try:
                int(meta['number'])
            except ValueError:
                if meta['number'] != '#':
                    issues.append(f"{rel_path}: 'number' must be an integer or '#'")

        # If it's an argument/modifier/sub-argument, it must reside inside a command directory
        if meta.get('type') in ('argument', 'modifier', 'sub-argument'):
            # Walk up until we find a parent .cdoc with command type
            parent_dir = os.path.dirname(file_path)
            found_command = False
            # Check up to 4 levels (command dir could be /commands/cmd_name/ or a bit deeper)
            for _ in range(4):
                if os.path.basename(parent_dir) in ('execute', 'execute_args', 'setup_args'):
                    parent_dir = os.path.dirname(parent_dir)
                    continue
                for f in os.listdir(parent_dir):
                    if f.endswith('.cdoc'):
                        parent_meta = parse_meta(os.path.join(parent_dir, f))
                        if parent_meta.get('type', '').startswith('command'):
                            found_command = True
                            break
                if found_command:
                    break
                parent_dir = os.path.dirname(parent_dir)
            if not found_command:
                # If this is a custom command extending a standard one,
                # try to find the parent in the standard commands directory.
                std_commands_dir = os.path.join(ROOT_PATH, 'apps', 'dev_patcher', 'core', 'commands')
                rel_to_ext = os.path.relpath(os.path.dirname(file_path),
                                             os.path.join(ROOT_PATH, 'extensions', 'custom_commands'))
                if not rel_to_ext.startswith('..'):
                    parts = rel_to_ext.replace('\\', '/').split('/')
                    try:
                        cmd_index = parts.index('commands')
                        if cmd_index + 1 < len(parts):
                            cmd_name = parts[cmd_index + 1]
                            std_cdoc = os.path.join(std_commands_dir, cmd_name, cmd_name + '.cdoc')
                            if os.path.exists(std_cdoc):
                                std_meta = parse_meta(std_cdoc)
                                if std_meta.get('type', '').startswith('command'):
                                    found_command = True
                    except ValueError:
                        pass
                if not found_command:
                    issues.append(f"{rel_path}: argument/modifier without a parent command .cdoc")

    # ---- .csdoc ----
    elif ext == '.csdoc':
        # csdoc files define sections/categories, must have 'category'
        if 'category' not in meta:
            issues.append(f"{rel_path}: missing 'category' field (required for .csdoc)")
        if 'number' not in meta:
            issues.append(f"{rel_path}: missing 'number' field")
        else:
            try:
                int(meta['number'])
            except ValueError:
                if meta['number'] != '#':
                    issues.append(f"{rel_path}: 'number' must be an integer or '#'")

    # ---- .exdoc ----
    elif ext == '.exdoc':
        # extension doc files, used for indexes like DevPatcher.exdoc
        if 'type' not in meta:
            issues.append(f"{rel_path}: missing 'type' field")
        if 'number' not in meta:
            issues.append(f"{rel_path}: missing 'number' field")
        # type format is flexible (e.g. app(DevPatcher)), so no strict check

    return issues

def scan_doc_files(root_path):
    """Recursively find all .cdoc, .csdoc, .exdoc files in relevant directories."""
    targets = []
    search_roots = [
        os.path.join(root_path, 'apps'),
        os.path.join(root_path, 'extensions', 'custom_commands'),
    ]
    for sr in search_roots:
        if not os.path.isdir(sr):
            continue
        for dirpath, _, filenames in os.walk(sr):
            for fn in filenames:
                if fn.endswith(('.cdoc', '.csdoc', '.exdoc')):
                    targets.append(os.path.join(dirpath, fn))
    return targets

def main():
    print("=" * 50)
    print("    Documentation File Validator (check_docs_files)")
    print("=" * 50)

    files = scan_doc_files(ROOT_PATH)
    if not files:
        print("[INFO] No doc files found.")
        sys.exit(0)

    all_issues = []
    for fp in files:
        rel = os.path.relpath(fp, ROOT_PATH)
        issues = validate_file(fp, rel)
        all_issues.extend(issues)

    if all_issues:
        for issue in all_issues:
            print(f"[FAIL] {issue}")
        sys.exit(1)
    else:
        print(f"[PASS] All {len(files)} doc files have valid metadata.")
        sys.exit(0)

if __name__ == '__main__':
    main()