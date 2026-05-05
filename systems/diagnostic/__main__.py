import os
import sys
from systems.diagnostic.runner import run_all_diagnostics

if __name__ == "__main__":
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    save_coverage = "--save-coverage" in sys.argv
    run_all_diagnostics(root_dir, save_coverage=save_coverage)