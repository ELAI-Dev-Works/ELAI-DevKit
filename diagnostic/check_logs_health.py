#!/usr/bin/env python3
"""
Diagnostic Script: Log Files Health Checker
-------------------------------------------
Checks that critical log files do not exceed safe size limits (5 MB).
Alerts if any log file is dangerously large or invalid.
"""
import os
import sys

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Define maximum size for a log file (in bytes)
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

LOG_FILES = [
    "logs/error_log.txt",
    "logs/crash_log.txt",
    "logs/translation_status.txt",
    "logs/diagnostic_result.txt",
    "logs/run_log.txt",
    "logs/thread_processing_log.txt",
]

def main():
    print("=" * 60)
    print("        Log Files Health Checker")
    print("=" * 60)
    errors = 0

    for rel_path in LOG_FILES:
        abs_path = os.path.join(ROOT_PATH, rel_path)
        if not os.path.exists(abs_path):
            print(f"[INFO] {rel_path} does not exist (may be normal).")
            continue

        try:
            size = os.path.getsize(abs_path)
        except OSError:
            print(f"[FAIL] Cannot access {rel_path}.")
            errors += 1
            continue

        if size > MAX_LOG_SIZE_BYTES:
            size_mb = size / (1024 * 1024)
            print(f"[WARNING] {rel_path} is {size_mb:.1f} MB (limit {MAX_LOG_SIZE_BYTES//(1024*1024)} MB). Consider archiving or deleting old logs.")
            errors += 1  # warning counts as a 'fail' for diagnostic visibility

    if errors:
        print("\n[FAIL] Some log files exceeded size limits or could not be checked.")
        sys.exit(1)
    else:
        print("[PASS] All log files are within size limits or absent.")
        sys.exit(0)

if __name__ == '__main__':
    main()