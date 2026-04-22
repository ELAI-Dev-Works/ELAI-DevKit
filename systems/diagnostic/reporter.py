import datetime
from typing import Dict, Any

def generate_report(results: Dict[str, Any], output_path: str):
    """
    Generates a structured text report from the diagnostic results.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("                       DIAGNOSTIC REPORT\n")
        f.write(f"                 Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        total_scripts = 0
        total_tests = 0
        passed_scripts = 0
        passed_tests = 0

        for category, data in results.items():
            f.write(f"[{category}]\n")
            f.write("-" * 70 + "\n")

            if data.get("scripts"):
                f.write("  Scripts:\n")
                for name, success, out, err in data["scripts"]:
                    total_scripts += 1
                    if success: passed_scripts += 1
                    status = "PASS" if success else "FAIL"
                    f.write(f"    - {name} [{status}]\n")

                    for line in out.splitlines():
                        if " [PASS] " in line or " [FAIL] " in line or " [ERROR] " in line:
                            f.write(f"        -> {line.strip()}\n")

                    if not success or "WARNING" in out.upper() or "WARNING" in err.upper():
                        f.write("      Output:\n")
                        combined_out = (out + "\n" + err).strip()
                        for line in combined_out.splitlines():
                            f.write(f"        {line}\n")
                        f.write("\n")

            if data.get("tests"):
                f.write("  Tests:\n")
                for name, success, out, err in data["tests"]:
                    total_tests += 1
                    if success: passed_tests += 1
                    status = "PASS" if success else "FAIL"
                    f.write(f"    - {name} [{status}]\n")

                    for line in err.splitlines():
                        if " ... ok" in line:
                            test_name = line.split(" ... ok")[0]
                            f.write(f"        -> {test_name.strip()} [PASS]\n")
                        elif " ... FAIL" in line:
                            test_name = line.split(" ... FAIL")[0]
                            f.write(f"        -> {test_name.strip()} [FAIL]\n")
                        elif " ... ERROR" in line:
                            test_name = line.split(" ... ERROR")[0]
                            f.write(f"        -> {test_name.strip()} [ERROR]\n")

                    if not success:
                        f.write("      Output:\n")
                        combined_out = (out + "\n" + err).strip()
                        for line in combined_out.splitlines():
                            f.write(f"        {line}\n")
                        f.write("\n")

            f.write("\n")

        f.write("=" * 70 + "\n")
        f.write("SUMMARY:\n")
        f.write(f"  Scripts: {passed_scripts}/{total_scripts} passed\n")
        f.write(f"  Tests:   {passed_tests}/{total_tests} passed\n")
        f.write("=" * 70 + "\n")