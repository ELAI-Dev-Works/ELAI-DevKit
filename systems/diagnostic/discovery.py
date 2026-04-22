import os
from typing import Dict, List, Any

def discover_diagnostics(root_path: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Scans the project for diagnostic scripts and tests.
    Returns a dictionary organized by category (Core, Apps, Extensions).
    """
    results = {}

    def scan_dir(base_dir: str, category_name: str):
        if not os.path.isdir(base_dir):
            return
            
        scripts = []
        tests =[]

        # Scan scripts directly in diagnostic/
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isfile(item_path) and item.endswith('.py') and item != '__init__.py':
                scripts.append(item_path)

        # Scan tests in diagnostic/tests/ recursively
        tests_dir = os.path.join(base_dir, 'tests')
        if os.path.isdir(tests_dir):
            for root_dir, _, files in os.walk(tests_dir):
                for item in files:
                    if item.endswith('.py') and item != '__init__.py':
                        tests.append(os.path.join(root_dir, item))

        if scripts or tests:
            results[category_name] = {"scripts": scripts, "tests": tests}

    # 1. Core Diagnostics
    scan_dir(os.path.join(root_path, 'diagnostic'), "Core")

    # 2. Apps Diagnostics
    apps_dir = os.path.join(root_path, 'apps')
    if os.path.isdir(apps_dir):
        for app in os.listdir(apps_dir):
            app_diag = os.path.join(apps_dir, app, 'diagnostic')
            scan_dir(app_diag, f"App: {app}")

    # 3. Custom Extensions Diagnostics
    ext_dir = os.path.join(root_path, 'extensions', 'custom_apps')
    if os.path.isdir(ext_dir):
        for ext in os.listdir(ext_dir):
            ext_diag = os.path.join(ext_dir, ext, 'diagnostic')
            scan_dir(ext_diag, f"Extension: {ext}")

    return results