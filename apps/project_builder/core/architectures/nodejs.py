import os
import subprocess
import shutil
from .base import BaseBuilder

class NodeJSBuilder(BaseBuilder):
    def build(self) -> bool:
        self.log("[NodeJS] Starting pkg build process...")
        
        if not shutil.which("npx"):
            self.log("[Error] 'npx' is not installed or not in PATH. Please install Node.js.")
            return False

        main_path = os.path.join(self.root_path, self.main_file)
        if not os.path.exists(main_path) and not os.path.exists(os.path.join(self.root_path, "package.json")):
            self.log(f"[Error] Entry point or package.json not found.")
            return False

        pkg_path = os.path.join(self.root_path, "package.json")
        if os.path.exists(pkg_path):
            try:
                import json
                with open(pkg_path, 'r', encoding='utf-8') as f:
                    pkg_data = json.load(f)

                app_name = self.options.get('app_name')
                if app_name:
                    pkg_data['name'] = app_name.lower().replace(" ", "-").replace("(", "").replace(")", "")

                app_version = self.options.get('app_version')
                if app_version:
                    pkg_data['version'] = app_version

                with open(pkg_path, 'w', encoding='utf-8') as f:
                    json.dump(pkg_data, f, indent=2)
            except Exception as e:
                self.log(f"[Warning] Failed to update package.json: {e}")

        app_icon = self.options.get('app_icon')
        if app_icon:
            self.log("[Warning] NodeJS (pkg) builder does not natively support setting executable icons without external tools like rcedit.")

        # Determine target
        target_os = self.options.get('target_os', 'windows')
        pkg_target = "node18-win-x64"
        if target_os == 'linux': pkg_target = "node18-linux-x64"
        elif target_os == 'mac': pkg_target = "node18-macos-x64"

        # --yes automatically accepts the prompt to download pkg if it's missing
        cmd = ["npx", "--yes", "pkg", ".", "--targets", pkg_target, "--out-path", self.output_dir]

        self.log(f"[NodeJS] Executing: {' '.join(cmd)}")
        
        process = subprocess.Popen(cmd, cwd=self.root_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', shell=True if os.name == 'nt' else False)
        
        for line in iter(process.stdout.readline, ''):
            self.log(line.strip())
            
        process.stdout.close()
        return_code = process.wait()
        
        if return_code == 0:
            self.log(f"[NodeJS] Build successful! Output saved to: {self.output_dir}")
            return True
        else:
            self.log(f"[Error] pkg exited with code {return_code}")
            return False