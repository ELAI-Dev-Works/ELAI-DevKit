import sys
import os
import subprocess
from typing import List
import shutil

class OSSandbox:
    """
    Layer 3 Security: OS-Level Isolation.
    Restricts write access strictly to the temp directory.
    """
    @staticmethod
    def wrap_command(cmd: List[str], temp_dir: str, is_trusted: bool = False) -> List[str]:
        if is_trusted:
            return cmd

        if sys.platform == 'linux':
            # Use bubblewrap (bwrap) if available
            if shutil.which('bwrap'):
                return [
                    'bwrap', '--ro-bind', '/', '/',
                    '--dev', '/dev', '--proc', '/proc',
                    '--tmpfs', '/tmp',
                    '--bind', temp_dir, temp_dir,
                    '--unshare-net', # Network is isolated by default at OS level, IPC allowed via localhost
                ] + cmd
        elif sys.platform == 'darwin':
            # macOS sandbox-exec
            if shutil.which('sandbox-exec'):
                profile = f"""
                (version 1)
                (allow default)
                (deny file-write* (subpath "/"))
                (allow file-write* (subpath "{temp_dir}"))
                (allow network*)
                """
                profile_path = os.path.join(temp_dir, '.mac_sandbox.sb')
                with open(profile_path, 'w') as f:
                    f.write(profile)
                return ['sandbox-exec', '-f', profile_path] + cmd
        
        # Windows: Full OS sandboxing in pure Python is complex.
        # We rely heavily on Layer 2 (Auditors) + ProcessManager Job Objects (already implemented in process_utils).
        return cmd