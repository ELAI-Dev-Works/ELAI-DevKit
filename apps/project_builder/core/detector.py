import os

class ProjectDetector:
    @staticmethod
    def detect(fs) -> dict:
        result = {
            "architecture": "unknown",
            "main_files": [],
            "has_venv": False,
            "has_node_modules": False
        }

        if not fs or not fs.exists(""):
            return result

        py_files = []
        js_files = []
        html_files = []

        for item in fs.listdir(""):
            if not fs.exists(item) or fs.is_dir(item): continue
            lower_item = item.lower()
            if lower_item.endswith('.py'): py_files.append(item)
            elif lower_item.endswith(('.js', '.ts')): js_files.append(item)
            elif lower_item.endswith('.html'): html_files.append(item)

        # Python Detection
        if fs.exists("requirements.txt") or py_files:
            result["architecture"] = "python"
            if "main.py" in py_files:
                result["main_files"] = ["main.py"] + [f for f in py_files if f != "main.py"]
            else:
                result["main_files"] = py_files
            if fs.exists(".venv"):
                result["has_venv"] = True

        # NodeJS Detection
        elif fs.exists("package.json"):
            result["architecture"] = "nodejs"
            try:
                import json
                pkg = json.loads(fs.read("package.json"))
                main_file = pkg.get('main', 'index.js')
                if main_file in js_files:
                    js_files.remove(main_file)
                    js_files.insert(0, main_file)
                elif main_file not in js_files and fs.exists(main_file):
                    js_files.insert(0, main_file)
            except Exception:
                pass
            result["main_files"] = js_files
            if fs.exists("node_modules"):
                result["has_node_modules"] = True

        # Web Detection
        elif html_files:
            result["architecture"] = "web"
            if "index.html" in html_files:
                result["main_files"] = ["index.html"] + [f for f in html_files if f != "index.html"]
            else:
                result["main_files"] = html_files

        return result