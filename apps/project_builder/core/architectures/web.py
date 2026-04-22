import os
import subprocess
import shutil
import json
from .base import BaseBuilder

class WebBuilder(BaseBuilder):
    def build(self) -> bool:
        self.log("[Web] Starting web package process via Electron...")

        if not shutil.which("npx"):
            self.log("[Error] 'npx' is not installed or not in PATH. Please install Node.js.")
            return False

        main_path = os.path.join(self.root_path, self.main_file)
        if not os.path.exists(main_path):
            self.log(f"[Error] Main file {self.main_file} not found.")
            return False

        stage_dir = os.path.join(self.output_dir, "electron_stage")
        if os.path.exists(stage_dir):
            shutil.rmtree(stage_dir)
        os.makedirs(stage_dir, exist_ok=True)

        self.log("[Web] Copying project files to staging directory...")
        for item in os.listdir(self.root_path):
            if item in['.git', '.venv', '__pycache__', 'node_modules', os.path.basename(self.output_dir)]:
                continue
            s = os.path.join(self.root_path, item)
            d = os.path.join(stage_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

        app_name = self.options.get('app_name') or 'WebApp'
        app_version = self.options.get('app_version') or '1.0.0'
        app_icon = self.options.get('app_icon')

        pkg_path = os.path.join(stage_dir, "package.json")
        if not os.path.exists(pkg_path):
            pkg_data = {
                "name": app_name.lower().replace(" ", "-").replace("(", "").replace(")", ""),
                "version": app_version,
                "main": "electron_main.js",
                "scripts": {
                    "start": "electron ."
                }
            }
            with open(pkg_path, "w", encoding="utf-8") as f:
                json.dump(pkg_data, f, indent=2)

        main_js_path = os.path.join(stage_dir, "electron_main.js")
        if not os.path.exists(main_js_path):
            main_js_code = f"""const {{ app, BrowserWindow }} = require('electron');
const path = require('path');

function createWindow () {{
  const win = new BrowserWindow({{
    width: 1280,
    height: 720,
    autoHideMenuBar: true,
    webPreferences: {{
      nodeIntegration: false,
      contextIsolation: true
    }}
  }});
  win.loadFile('{self.main_file}');
}}

app.whenReady().then(() => {{
  createWindow();
  app.on('activate', function () {{
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  }});
}});

app.on('window-all-closed', function () {{
  if (process.platform !== 'darwin') app.quit();
}});
"""
            with open(main_js_path, "w", encoding="utf-8") as f:
                f.write(main_js_code)

        target_os = self.options.get('target_os', 'windows')
        platform = "win32"
        if target_os == 'linux': platform = "linux"
        elif target_os == 'mac': platform = "darwin"

        self.log("[Web] Installing Electron...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.run([npm_cmd, "install", "electron", "electron-packager", "--save-dev"], cwd=stage_dir, capture_output=True)

        self.log(f"[Web] Packaging for {platform}...")
        npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
        cmd =[npx_cmd, "electron-packager", ".", app_name, "--platform=" + platform, "--arch=x64", "--app-version=" + app_version, "--out=" + self.output_dir, "--overwrite"]

        if app_icon and os.path.exists(app_icon):
            cmd.append("--icon=" + app_icon)

        self.log(f"[Web] Executing: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, cwd=stage_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')

        for line in iter(process.stdout.readline, ''):
            self.log(line.strip())

        process.stdout.close()
        return_code = process.wait()

        try:
            shutil.rmtree(stage_dir)
        except:
            pass

        if return_code == 0:
            self.log(f"[Web] Build successful! Output saved to: {self.output_dir}")
            return True
        else:
            self.log(f"[Error] Electron Packager exited with code {return_code}")
            return False