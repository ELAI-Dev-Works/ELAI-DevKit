#!/usr/bin/env python3
"""
Diagnostic Script: Settings Validator
--------------------------------------
Validates the application's `settings.toml` (and optionally the current
project's `project_settings.toml`) for structural integrity and common issues.
"""

import os
import sys
import tomllib

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def validate_settings(filepath, label):
    print(f"\n--- Validating {label} ---")
    if not os.path.exists(filepath):
        print(f"[WARNING] File not found: {filepath}")
        return False

    try:
        with open(filepath, 'rb') as f:
            data = tomllib.load(f)
        print(f"[PASS] File is valid TOML.")
        return True
    except tomllib.TOMLDecodeError as e:
        print(f"[FAIL] TOML Syntax Error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False

def check_required_keys(data, path=''):
    """Check for required top-level structure and common misconfigurations."""
    issues = []
    if 'core' in data:
        core = data['core']
        if 'theme' in core:
            theme = core['theme']
            valid_colors = ['dark', 'light', 'ocean']
            valid_styles = ['basic', 'clean', 'sleek']
            color = theme.get('color_scheme')
            style = theme.get('theme')
            if color is not None and color not in valid_colors:
                issues.append(f"[WARNING] core.theme.color_scheme '{color}' is not a standard value ({', '.join(valid_colors)}).")
            if style is not None and style not in valid_styles:
                issues.append(f"[WARNING] core.theme.theme '{style}' is not a standard value ({', '.join(valid_styles)}).")
        if 'extensions' in core:
            for ext_name, enabled in core['extensions'].items():
                if not isinstance(enabled, bool):
                    issues.append(f"[WARNING] core.extensions.{ext_name} should be a boolean (true/false).")
    else:
        issues.append("[WARNING] Missing top-level [core] section.")
    return issues

def main():
    print("========================================")
    print("         Settings Validator")
    print("========================================")
    settings_path = os.path.join(ROOT_PATH, 'config', 'settings.toml')
    global_valid = validate_settings(settings_path, "Global settings.toml")

    # Attempt to load and check structure if valid
    if global_valid:
        try:
            with open(settings_path, 'rb') as f:
                data = tomllib.load(f)
            issues = check_required_keys(data)
            for issue in issues:
                print(issue)
            if not issues:
                print("[PASS] No structural issues found in global settings.")
        except Exception as e:
            print(f"[ERROR] Could not re-parse for key check: {e}")

    # Optionally check project settings (if a project path is provided via environment or argument)
    project_path = None
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        # Try to deduce from environment if running in the context of the app
        project_path = os.environ.get('ELAI_PROJECT_PATH')

    if project_path and os.path.isdir(project_path):
        proj_settings = os.path.join(project_path, 'project_settings.toml')
        if os.path.exists(proj_settings):
            validate_settings(proj_settings, f"Project settings ({project_path})")
        else:
            print(f"[INFO] No project_settings.toml found in {project_path}.")
    else:
        print("[INFO] No project path specified for project settings validation.")

    print("\nValidation complete.")

if __name__ == '__main__':
    main()