import unittest
import os
import tempfile
import shutil
import tomllib
from systems.settings.manager import SettingsManager

class TestSettingsManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="elai_sett_")
        self.config_dir = os.path.join(self.temp_dir, "config")
        self.user_dir = os.path.join(self.temp_dir, "user")
        os.makedirs(self.config_dir)
        # Create a minimal settings.toml
        self.settings_path = os.path.join(self.config_dir, "settings.toml")
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            f.write('[core]\nlanguage = "en"\n')
        
        self.manager = SettingsManager(self.temp_dir)
        self.manager.settings_path = self.settings_path

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_load_defaults_with_merge(self):
        defaults = {"language": "de", "theme": {"color": "dark"}}
        custom = {"language": "en"}
        merged = self.manager._deep_merge(defaults, custom)
        self.assertEqual(merged["language"], "en")
        self.assertEqual(merged["theme"]["color"], "dark")

    def test_02_get_setting_with_project_override(self):
        # Write project settings
        proj_path = os.path.join(self.temp_dir, "project")
        os.makedirs(proj_path)
        self.manager.set_project_path(proj_path)
        default_settings = {
            "core": {
                "ignore": {
                    "dirs": [".venv"],
                    "files": ["*.pyc"],
                    "use_gitignore": False
                }
            }
        }
        # Set global ignore in memory
        self.manager._settings_cache = default_settings
        # Set project override in memory
        project_override = {
            "core": {
                "project_ignore": {
                    "dirs": [".env"],
                    "files": [],
                }
            }
        }
        self.manager._project_settings_cache = project_override
        
        ignored = self.manager.get_ignore_lists()
        g_dirs, g_files, use_git, p_dirs, p_files = ignored
        self.assertIn(".venv", g_dirs)
        self.assertIn(".env", p_dirs)
        self.assertEqual(len(p_files), 0)

    def test_03_nested_set_and_get(self):
        self.manager._settings_cache = {}
        self.manager.update_setting(["core", "extensions"], {"dev_patcher": True})
        # Verify direct memory update
        self.assertTrue(self.manager._settings_cache["core"]["extensions"]["dev_patcher"])

    def test_04_raw_toml_parsing(self):
        toml_str = '[core]\nname = "myset"\n[core.nested]\nkey = 123\n'
        with open(self.settings_path, 'w') as f:
            f.write(toml_str)
        # Force reload
        self.manager._settings_cache = None
        settings = self.manager.load_settings_file()
        self.assertEqual(settings["core"]["name"], "myset")
        self.assertEqual(settings["core"]["nested"]["key"], 123)

if __name__ == '__main__':
    unittest.main()