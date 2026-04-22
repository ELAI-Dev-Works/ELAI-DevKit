import os

class DocManager:
    def __init__(self, app_root_path):
        self.app_root_path = app_root_path
        self.docs = {} # { 'Category/Extension': { 'Title': 'Path' } }

    def scan_docs(self, project_path=None):
        """Scans for .md files in apps/*/doc, extensions/*/doc and project/custom_commands/*/doc."""
        self.docs = {}
    
        # 1. Scan Core Apps
        core_apps_path = os.path.join(self.app_root_path, "apps")
        self._scan_directory(core_apps_path, "Core Apps")
    
        # 2. Scan Custom Extensions
        extensions_path = os.path.join(self.app_root_path, "extensions", "custom_apps")
        self._scan_directory(extensions_path, "Extensions")
        
        # 3. Scan Custom Commands (Project Level)
        if project_path:
            custom_commands_path = os.path.join(project_path, "extensions", "custom_commands")
            self._scan_directory(custom_commands_path, "Custom Commands")
        
        return self.docs

    def _scan_directory(self, base_path, category_prefix):
        if not os.path.exists(base_path):
            return

        for ext_name in os.listdir(base_path):
            doc_path = os.path.join(base_path, ext_name, "doc")
            if os.path.isdir(doc_path):
                display_name = ext_name.replace('_', ' ').title()
                category = f"{category_prefix}/{display_name}"
                self.docs[category] = {}

                for root, dirs, files in os.walk(doc_path):
                    for file in files:
                        if file.endswith(".md"):
                            full_path = os.path.join(root, file)
                            # Create a readable title from filename
                            title = os.path.splitext(file)[0].replace('_', ' ').title()
                            
                            # Determine the full category path including subdirectories
                            current_category = category
                            rel_dir = os.path.relpath(root, doc_path)
                            
                            if rel_dir != ".":
                                # Convert subdirectories into category levels
                                sub_cat_parts = rel_dir.replace(os.sep, '/').split('/')
                                formatted_parts = [p.replace('_', ' ').title() for p in sub_cat_parts]
                                current_category = f"{category}/{'/'.join(formatted_parts)}"

                            # Ensure category dict exists
                            if current_category not in self.docs:
                                self.docs[current_category] = {}

                            self.docs[current_category][title] = full_path