import os
import json

class MetadataLoader:
    """
    Handles parsing, validation, and normalization of extension metadata.
    """
    
    DEFAULT_META = {
        "name": "unknown",
        "display_name": "Unknown Extension",
        "author": "Unknown",
        "version": "0.0.0",
        "dependencies": [],
        "conflicts": [],  # New: Extensions that this one conflicts with
        "description": "No description provided.",
        "enabled": True,
        "is_core": False,
        "path": "",
        "structure_version": 1
    }

    @staticmethod
    def load_metadata(path, folder_name, is_core):
        """
        Loads metadata.json if present, otherwise generates default metadata based on folder structure.
        """
        meta = MetadataLoader.DEFAULT_META.copy()
        meta["name"] = folder_name
        meta["display_name"] = folder_name.replace('_', ' ').title()
        meta["path"] = path
        meta["is_core"] = is_core

        # Detect Architecture Version based on file structure
        # V2 has gui/windows/core.py
        if os.path.exists(os.path.join(path, "gui", "windows", "core.py")):
            meta["structure_version"] = 2
        else:
            meta["structure_version"] = 1

        metadata_json_path = os.path.join(path, "metadata.json")
        if os.path.exists(metadata_json_path):
            try:
                with open(metadata_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Merge JSON data into meta dict
                    for key, value in data.items():
                        if key == "name":
                            meta["display_name"] = value # JSON 'name' is usually display name
                        else:
                            meta[key] = value
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[Metadata] Warning: Could not parse metadata for '{folder_name}': {e}")

        return meta