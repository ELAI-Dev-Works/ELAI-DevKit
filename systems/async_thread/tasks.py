import subprocess
import os
from typing import Generator
from .process_utils import ProcessManager

class SubprocessStreamTask:
    """
    A pre-built task for running subprocesses and streaming their output.
    Designed to be directly executed by ThreadControl.run_in_background.
    
    Usage:
    task = SubprocessStreamTask(["ping", "8.8.8.8"])
    thread_control.run_in_background(task, yield_callback=print)
    """
    def __init__(self, cmd: list, cwd: str = None, env: dict = None, encoding: str = 'utf-8'):
        self.cmd = cmd
        self.cwd = cwd or os.getcwd()
        self.env = env or os.environ.copy()
        self.encoding = encoding

    def __call__(self, worker_ref=None, *args, **kwargs) -> Generator[str, None, int]:
        """
        Executes the subprocess. Yields stdout lines.
        Returns the process return code when finished.
        """
        from systems.error_handler.thread_tracer import ThreadTracer
        cmd_str = " ".join(self.cmd)
        ThreadTracer.log_action("subprocess", cmd_str, "Subprocess stream task started")

        process = None
        try:
            # Hide console window on Windows
            creationflags = ProcessManager.get_creation_flags()
            
            process = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=self.encoding,
                errors='replace',
                creationflags=creationflags
            )

            ProcessManager.register_process(process.pid)

            # Stream output
            for line in process.stdout:
                # Check for cancellation from the ThreadControl worker
                if worker_ref and getattr(worker_ref, 'is_cancelled', False):
                    ProcessManager.kill_process_tree(process.pid)
                    yield "[System] Process cancelled by user."
                    return -1

                yield line.strip()

            process.stdout.close()
            return_code = process.wait()

            # Final check in case cancelled exactly at the end
            if worker_ref and getattr(worker_ref, 'is_cancelled', False):
                ThreadTracer.log_action("subprocess", cmd_str, "Subprocess stream task cancelled at the end")
                return -1

            ThreadTracer.log_action("subprocess", cmd_str, f"Subprocess stream task finished with return code {return_code}")
            return return_code

        except Exception as e:
            ThreadTracer.log_action("subprocess", cmd_str, f"Subprocess stream task failed: {e}")
            if process:
                ProcessManager.kill_process_tree(process.pid)
            raise RuntimeError(f"Subprocess failed: {e}")
        finally:
            if process:
                ProcessManager.unregister_process(process.pid)