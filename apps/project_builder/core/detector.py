import os

class ProjectDetector:
    @staticmethod
    def detect(root_path: str) -> dict:
        result = {
            "architecture": "unknown",
            "main_files": [],
            "has_venv": False,
            "has_node_modules": False
        }

        if not root_path or not os.path.exists(root_path):
            return result

        py_files = []
        js_files = []
        html_files = []

        for item in os.listdir(root_path):
            if not os.path.isfile(os.path.join(root_path, item)): continue
            lower_item = item.lower()
            if lower_item.endswith('.py'): py_files.append(item)
            elif lower_item.endswith(('.js', '.ts')): js_files.append(item)
            elif lower_item.endswith('.html'): html_files.append(item)

        # Python Detection
        if os.path.exists(os.path.join(root_path, "requirements.txt")) or py_files:
            result["architecture"] = "python"
            if "main.py" in py_files:
                result["main_files"] = ["main.py"] + [f for f in py_files if f != "main.py"]
            else:
                result["main_files"] = py_files
            if os.path.exists(os.path.join(root_path, ".venv")):
                result["has_venv"] = True

        # NodeJS Detection
        elif os.path.exists(os.path.join(root_path, "package.json")):
            result["architecture"] = "nodejs"
            try:
                import json
                with open(os.path.join(root_path, "package.json"), 'r', encoding='utf-8') as f:
                    pkg = json.load(f)
                    main_file = pkg.get('main', 'index.js')
                    if main_file in js_files:
                        js_files.remove(main_file)
                        js_files.insert(0, main_file)
                    elif main_file not in js_files and os.path.exists(os.path.join(root_path, main_file)):
                        js_files.insert(0, main_file)
            except Exception:
                pass
            result["main_files"] = js_files
            if os.path.exists(os.path.join(root_path, "node_modules")):
                result["has_node_modules"] = True

        # Web Detection
        elif html_files:
            result["architecture"] = "web"
            if "index.html" in html_files:
                result["main_files"] = ["index.html"] + [f for f in html_files if f != "index.html"]
            else:
                result["main_files"] = html_files

        return result