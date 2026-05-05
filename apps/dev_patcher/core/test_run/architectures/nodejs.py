import os
from systems.os.platform import is_windows
from .base import BaseArchitecture

class NodeJSArchitecture(BaseArchitecture):
    def get_launch_command(self, is_trusted=False):
        exe = "node" if self.launch_file.endswith(".js") else "ts-node"

        native_sec_flags = []
        warning_cmd = ""
        try:
            import subprocess
            # Detect if Node supports the native Permission Model (v20+)
            res = subprocess.run([exe, "-v"], capture_output=True, text=True)
            if res.returncode == 0:
                version_str = res.stdout.strip()
                if version_str.startswith("v"):
                    major = int(version_str[1:].split('.')[0])
                    if major >= 20 and not is_trusted:
                        # Apply Node 20/22+ Native C++ Engine Sandbox
                        native_sec_flags = ["--experimental-permission", "--allow-fs-read=*", f"--allow-fs-write={self.temp_dir}"]
                    elif not is_trusted:
                        warning_msg = f"[SECURITY WARNING] Node.js version {version_str} lacks native sandbox support. JS hooks provide only an illusion of safety. Upgrade to Node 20+!"
                        warning_cmd = f"echo \"{warning_msg}\"; "
        except Exception:
            pass

        cmd_list = [exe] + native_sec_flags + [self.launch_file]
        cmd_list = self._apply_sandbox(cmd_list, is_trusted)

        if is_windows():
            cmd_str = " ".join(f'"{c}"' for c in cmd_list)
            return f"{warning_cmd}& {cmd_str}"
        else:
            import shlex
            cmd_str = " ".join(shlex.quote(c) for c in cmd_list)
            return f"{warning_cmd}{cmd_str}"