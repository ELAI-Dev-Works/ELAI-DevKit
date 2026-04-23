import tomllib
import os
from typing import Dict, Any, List

# --- Minimal TOML Writer ---
# This is a basic TOML writer that handles the nested dictionary structure of the settings.
# It is not a general-purpose TOML writer.

def _format_toml_value(value):
    if isinstance(value, str):
        if '\n' in value or '\r' in value:
            if "'''" not in value and not value.endswith("'"):
                return f"'''\n{value}'''"
            else:
                escaped_value = value.replace('\\', '\\\\').replace('"""', '\\"\\"\\"').replace('\r', '')
                if escaped_value.endswith('"'):
                    escaped_value = escaped_value[:-1] + '\\"'
                return f'"""\n{escaped_value}"""'
        # Basic escaping for quotes and backslashes
        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped_value}"'
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return f"[{', '.join(_format_toml_value(v) for v in value)}]"
    return str(value)

def _save_toml_data(data: dict, path: str):
    with open(path, 'w', encoding='utf-8') as f:
        # Sort top-level keys for consistent output, with 'core' first.
        sorted_keys = sorted(data.keys(), key=lambda k: (k != 'core', k))

        for key in sorted_keys:
            value = data[key]
            if isinstance(value, dict):
                # This will handle nested tables like [core.theme]
                _write_toml_section(f, key, value)

def _write_toml_section(f, section_name, section_data):
    if not isinstance(section_data, dict):
        return

    # Split into sub-tables and direct key-value pairs
    sub_tables = {k: v for k, v in section_data.items() if isinstance(v, dict)}
    direct_items = {k: v for k, v in section_data.items() if not isinstance(v, dict)}

    if direct_items:
        f.write(f"\n[{section_name}]\n")
        for k, v in direct_items.items():
            f.write(f"  {k} = {_format_toml_value(v)}\n")

    # Recursively write sub-tables
    for k, v in sorted(sub_tables.items()):
        _write_toml_section(f, f"{section_name}.{k}", v)

class SettingsManager:
    def __init__(self, app_root_path: str):
        self.app_root_path = app_root_path
        self.config_dir = os.path.join(self.app_root_path, 'config')
        self.settings_path = os.path.join(self.config_dir, 'settings.toml')
        os.makedirs(self.config_dir, exist_ok=True)
        self._settings_cache = None

    def _get_nested(self, data: Dict, keys: List[str]):
        """Safely traverses a nested dictionary."""
        for key in keys:
            data = data.get(key, {})
        return data

    def _set_nested(self, data: Dict, keys: List[str], value: Dict):
        """Sets a value in a nested dictionary, creating keys if they don't exist."""
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value

    def _deep_merge(self, default: Dict, custom: Dict) -> Dict:
        """Recursively merges two dictionaries."""
        merged = default.copy()
        for key, value in custom.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def load_settings_file(self) -> Dict:
        """Loads the entire settings.toml file into a cache."""
        if self._settings_cache is not None:
            return self._settings_cache

        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'rb') as f:
                self._settings_cache = tomllib.load(f)
        else:
            self._settings_cache = {}
        
        return self._settings_cache

    def save_settings_file(self):
        """Saves the entire settings cache to settings.toml."""
        if self._settings_cache is not None:
            _save_toml_data(self._settings_cache, self.settings_path)

    def get_setting(self, keys: List[str], defaults: Dict) -> Dict:
        """
        Gets a specific section of the settings, merged with provided defaults.
        """
        all_settings = self.load_settings_file()
        custom_settings = self._get_nested(all_settings, keys)
        return self._deep_merge(defaults, custom_settings)

    def update_setting(self, keys: List[str], data_to_save: Dict):
        """
        Updates a section of the settings in the cache.
        Call save_settings_file() to commit changes to disk.
        """
        all_settings = self.load_settings_file()
        self._set_nested(all_settings, keys, data_to_save)
        self._settings_cache = all_settings

    def get_ignore_lists(self) -> (list[str], list[str], bool):
        """
        Loads and parses the ignore settings.
        Returns: (global_dirs, global_files, use_gitignore)
        """
        defaults = {
            'dirs': [".venv", "__pycache__", ".idea", "build", "dist", "node_modules"],
            'files': ["*.pyc", "*.log*", ".env"],
            'use_gitignore': False
        }
        ignore_settings = self.get_setting(['core', 'ignore'], defaults)
    
        return (
            ignore_settings.get('dirs', []), 
            ignore_settings.get('files', []),
            ignore_settings.get('use_gitignore', False)
        )