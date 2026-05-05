#!/usr/bin/env python3
"""
Diagnostic Script: Project Text Packer Tester
Tests the file collection and tree building logic.
"""
import os
import sys

# Ensure the project root is in sys.path
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

import tempfile
from unittest.mock import MagicMock
from apps.project_text_packer.app import ProjectTextPackerApp
from systems.project.ignore_handler import IgnoreHandler
from systems.fs.real_fs import RealFileSystem

def test_collect_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_dir = os.path.join(tmpdir, "test_proj")
        os.makedirs(os.path.join(proj_dir, "src"))
        with open(os.path.join(proj_dir, "main.py"), 'w') as f:
            f.write("print('hello')")
        with open(os.path.join(proj_dir, "readme.md"), 'w') as f:
            f.write("# Readme")
        os.makedirs(os.path.join(proj_dir, ".git"))
        with open(os.path.join(proj_dir, ".git", "config"), 'w') as f:
            f.write("[core]")

        mock_context = MagicMock()
        mock_context.main_window = None
        mock_context.settings_manager.get_setting.return_value = {
            'supported_extensions': '.py .md .txt'
        }
        app = ProjectTextPackerApp(mock_context)
        app.root_path = proj_dir
        fs = RealFileSystem(proj_dir)
        handler = IgnoreHandler([], [], context='packer')

        collected = app.collect_files(fs, handler)
        rel_paths = set(rel for _, rel in collected)

        if "main.py" not in rel_paths:
            return False, "main.py not collected"
        if "readme.md" not in rel_paths:
            return False, "readme.md not collected"

        tree = app._build_tree_recursive(fs, "", handler)
        if not tree:
            return False, "Tree builder returned empty"
        return True, "Packer collection and tree OK"

def main():
    print("=" * 50)
    print("    Project Text Packer Tester")
    print("=" * 50)
    success, msg = test_collect_files()
    if success:
        print(f"[PASS] {msg}")
        sys.exit(0)
    else:
        print(f"[FAIL] {msg}")
        sys.exit(1)

if __name__ == '__main__':
    main()