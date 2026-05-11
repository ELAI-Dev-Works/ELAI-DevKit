import os
from systems.os.platform import is_windows

class ScriptManager:
    @staticmethod
    def create_bootstrap(fs):
        if is_windows():
            filename = "run.bat"
            content = "@echo off\nsetlocal\necho [ELAI] Auto-generated run.bat\n"
            if fs.exists('package.json'):
                 content += "echo Installing dependencies...\ncall npm install\necho Starting...\nnpm start\n"
            else:
                 content += "echo Preparing environment...\npython -m venv .venv\n.\\.venv\\Scripts\\pip.exe install -r requirements.txt\n.\\.venv\\Scripts\\python.exe main.py\n"
            content += "pause\n"
        else:
            filename = "run.sh"
            content = "#!/bin/bash\n\n"
            if fs.exists('package.json'):
                 content += "echo 'Installing dependencies...'\nnpm install\necho 'Starting...'\nnpm start\n"
            else:
                 content += "echo 'Preparing environment...'\npython3 -m venv .venv\n./.venv/bin/pip install -r requirements.txt\n./.venv/bin/python main.py\n"
            content += "read -p 'Press Enter to exit...' arg\n"

        try:
            if filename.endswith('.sh'):
                fs.write_bytes(filename, content.replace('\r\n', '\n').encode('utf-8'))
            else:
                fs.write(filename, content)

            if not is_windows():
                os.chmod(fs._to_abs(filename), 0o755)
            
            return filename
        except Exception as e:
            raise Exception(f"Failed to create bootstrap script: {e}")

    @staticmethod
    def ensure_args_support(full_path):
        if not os.path.exists(full_path): return
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return

        modified = False
        lines = content.splitlines()

        if full_path.lower().endswith(('.bat', '.cmd')):
            if '%*' not in content:
                last_exec_idx = -1
                for i, line in enumerate(lines):
                    stripped = line.strip().lower()
                    if ('python' in stripped or 'node' in stripped or 'uv run' in stripped or 'pytest' in stripped) \
                       and not stripped.startswith(('echo', 'rem', 'set', 'if', 'goto', 'call')) \
                       and ' venv ' not in stripped and ' pip ' not in stripped and ' npm ' not in stripped:
                        last_exec_idx = i
                if last_exec_idx != -1:
                    lines[last_exec_idx] = lines[last_exec_idx] + " %*"
                    modified = True

        elif full_path.lower().endswith('.sh'):
            if '"$@"' not in content and '$@' not in content:
                last_exec_idx = -1
                for i, line in enumerate(lines):
                    stripped = line.strip().lower()
                    if ('python' in stripped or 'node' in stripped or 'uv run' in stripped or 'pytest' in stripped) \
                       and not stripped.startswith(('echo', '#', 'export', 'if', 'set')) \
                       and ' venv ' not in stripped and ' pip ' not in stripped and ' npm ' not in stripped:
                        last_exec_idx = i
                if last_exec_idx != -1:
                    lines[last_exec_idx] = lines[last_exec_idx] + ' "$@"'
                    modified = True

        if modified:
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines) + '\n')
            except Exception:
                pass