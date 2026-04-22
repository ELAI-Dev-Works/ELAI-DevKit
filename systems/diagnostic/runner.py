import os
from .discovery import discover_diagnostics
from .executor import execute_script, execute_test
from .reporter import generate_report

def run_all_diagnostics(root_path: str):
    """
    Orchestrates the discovery, execution, and reporting of all diagnostics.
    """
    print("============================================")
    print("      ELAI-DevKit Diagnostic Runner")
    print("============================================\n")
    
    print("Scanning for diagnostic scripts and tests...")
    discovered = discover_diagnostics(root_path)

    if not discovered:
        print("No diagnostics found.")
        return

    results = {}

    for category, items in discovered.items():
        print(f"\nProcessing {category}...")
        cat_results = {"scripts": [], "tests":[]}

        for script in items.get("scripts",[]):
            name = os.path.basename(script)
            print(f"  Running script: {name}...", end="", flush=True)
            success, out, err = execute_script(script, root_path)
            status = "OK" if success else "FAILED"
            print(f"[{status}]")
            cat_results["scripts"].append((name, success, out, err))

        for test in items.get("tests",[]):
            name = os.path.basename(test)
            print(f"  Running test: {name}...", end="", flush=True)
            success, out, err = execute_test(test, root_path)
            status = "OK" if success else "FAILED"
            print(f" [{status}]")
            cat_results["tests"].append((name, success, out, err))

        results[category] = cat_results

    logs_dir = os.path.join(root_path, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    output_path = os.path.join(logs_dir, "diagnostic_result.txt")
    generate_report(results, output_path)
    print(f"\nDiagnostics complete. Detailed report saved to: {output_path}\n")