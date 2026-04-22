import os
from systems.diagnostic.runner import run_all_diagnostics

if __name__ == "__main__":
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    run_all_diagnostics(root_dir)