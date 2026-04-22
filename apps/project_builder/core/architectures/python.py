import os
import subprocess
import sys
from .base import BaseBuilder
from systems.os.platform import get_venv_python_path

class PythonBuilder(BaseBuilder):
    def build(self) -> bool:
        self.log("[Python] Starting PyInstaller build process...")

        main_path = os.path.join(self.root_path, self.main_file)
        if not os.path.exists(main_path):
            self.log(f"[Error] Main file not found: {main_path}")
            return False

        devkit_py = sys.executable

        # Project venv path for finding target dependencies
        venv_py = get_venv_python_path(self.root_path)

        env = os.environ.copy()

        if os.path.exists(venv_py):
            self.log(f"[Python] Using project's Python with DevKit's PyInstaller.")
            py_exe = venv_py

            try:
                import PyInstaller
                devkit_site_packages = os.path.dirname(os.path.dirname(PyInstaller.__file__))
                existing_pp = env.get('PYTHONPATH', '')
                env['PYTHONPATH'] = f"{devkit_site_packages}{os.pathsep}{existing_pp}" if existing_pp else devkit_site_packages
            except ImportError:
                self.log("[Error] PyInstaller not found in DevKit.")
                return False
        else:
            self.log("[Warning] Project virtual environment not found. Building with DevKit's Python.")
            py_exe = devkit_py

        # Build command
        cmd = [py_exe, "-m", "PyInstaller", "--distpath", self.output_dir, "--workpath", os.path.join(self.output_dir, "build")]

        if self.options.get('one_file', True):
            cmd.append("--onefile")
        if self.options.get('no_console', False):
            cmd.append("--windowed")

        app_name = self.options.get('app_name')
        if app_name:
            cmd.append(f"--name={app_name}")

        app_icon = self.options.get('app_icon')
        if app_icon and os.path.exists(app_icon):
            cmd.append(f"--icon={app_icon}")

        cmd.append(self.main_file)

        self.log(f"[Python] Executing: {' '.join(cmd)}")

        process = subprocess.Popen(cmd, cwd=self.root_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', env=env)
        
        for line in iter(process.stdout.readline, ''):
            self.log(line.strip())
            
        process.stdout.close()
        return_code = process.wait()
        
        if return_code == 0:
            self.log(f"[Python] Build successful! Output saved to: {self.output_dir}")
            return True
        else:
            self.log(f"[Error] PyInstaller exited with code {return_code}")
            return False