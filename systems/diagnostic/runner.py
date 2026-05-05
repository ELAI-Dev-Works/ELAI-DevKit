import os
import shutil
import sys
import subprocess
import concurrent.futures
from .discovery import discover_diagnostics
from .executor import execute_script, execute_test
from .reporter import generate_report
from systems.async_thread.thread_control import ThreadControl

def run_all_diagnostics(root_path: str, save_coverage: bool = False):
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

    # Create isolated temporary directory inside the project root
    diag_dir = os.path.join(root_path, ".diagnostic")
    os.makedirs(diag_dir, exist_ok=True)

    # Redirect system temp variables so subprocesses use our folder
    old_tmp = os.environ.get("TMP")
    old_temp = os.environ.get("TEMP")
    old_tmpdir = os.environ.get("TMPDIR")
    os.environ["TMP"] = diag_dir
    os.environ["TEMP"] = diag_dir
    os.environ["TMPDIR"] = diag_dir
    os.environ["COVERAGE_FILE"] = os.path.join(diag_dir, ".coverage")

    try:
        subprocess.run([sys.executable, "-m", "coverage", "erase"], cwd=root_path)
        tc = ThreadControl()

        for category, items in discovered.items():
            print(f"\nProcessing {category}...")
            cat_results = {"scripts": [], "tests":[]}
            workers = []

            for script in items.get("scripts",[]):
                name = os.path.basename(script)
                worker = tc.run_in_background(execute_script, use_qt=False, script_path=script, root_path=root_path)
                workers.append(("script", name, worker))

            for test in items.get("tests",[]):
                name = os.path.basename(test)
                worker = tc.run_in_background(execute_test, use_qt=False, test_path=test, root_path=root_path)
                workers.append(("test", name, worker))

            for w_type, name, worker in workers:
                try:
                    success, out, err = worker.future.result(timeout=120)
                    status = "OK" if success else "FAILED"
                    print(f"  Finished {w_type}: {name} [{status}]")
                    if w_type == "script":
                        cat_results["scripts"].append((name, success, out, err))
                    else:
                        cat_results["tests"].append((name, success, out, err))
                except concurrent.futures.TimeoutError:
                    print(f"  Finished {w_type}: {name} [TIMEOUT]")
                    cat_results["scripts" if w_type == "script" else "tests"].append(
                        (name, False, "", "Execution timed out (30s).")
                    )
                except Exception as e:
                    print(f"  Failed {w_type}: {name} [ERROR: {e}]")

            results[category] = cat_results

        tc.shutdown()

        logs_dir = os.path.join(root_path, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        output_path = os.path.join(logs_dir, "diagnostic_result.txt")
        generate_report(results, output_path)

        print("Combining coverage data and generating report...")
        subprocess.run([sys.executable, "-m", "coverage", "combine"], cwd=root_path, capture_output=True)
        cov_result = subprocess.run([sys.executable, "-m", "coverage", "report"], cwd=root_path, capture_output=True, text=True)
        if cov_result.returncode == 0:
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write("\n" + "=" * 70 + "\n")
                f.write("                       CODE COVERAGE SUMMARY\n")
                f.write("=" * 70 + "\n\n")
                f.write(cov_result.stdout)
        else:
            print(f"Coverage report generation failed: {cov_result.stderr}")

        print(f"\nDiagnostics complete. Detailed report saved to: {output_path}\n")
    finally:
        # Restore original environment variables
        if old_tmp is None:
            if "TMP" in os.environ:
                del os.environ["TMP"]
        else:
            os.environ["TMP"] = old_tmp

        if old_temp is None:
            if "TEMP" in os.environ:
                del os.environ["TEMP"]
        else:
            os.environ["TEMP"] = old_temp

        if old_tmpdir is None:
            if "TMPDIR" in os.environ:
                del os.environ["TMPDIR"]
        else:
            os.environ["TMPDIR"] = old_tmpdir

        if "COVERAGE_FILE" in os.environ:
            del os.environ["COVERAGE_FILE"]

        if save_coverage:
            cov_path = os.path.join(diag_dir, ".coverage")
            if os.path.exists(cov_path):
                shutil.copy2(cov_path, os.path.join(root_path, ".coverage"))
                print("\nSaved .coverage file to project root.")

        shutil.rmtree(diag_dir, ignore_errors=True)