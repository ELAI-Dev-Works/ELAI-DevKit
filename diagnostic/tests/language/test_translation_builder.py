import unittest
import os
import json
import tempfile
import shutil
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from systems.language.builder import TranslationBuilder
from systems.language.manager import LanguageManager

class TestTranslationBuilder(unittest.TestCase):

    def setUp(self):
        self.temp_root = tempfile.mkdtemp(prefix="elai_lang_test_")
        self.addCleanup(shutil.rmtree, self.temp_root, ignore_errors=True)

        # Create minimal structure
        self.lang_dir = os.path.join(self.temp_root, "lang")
        os.makedirs(self.lang_dir)

        # Create a .tslang file
        self.ts_dir = os.path.join(self.temp_root, "assets", "translation")
        os.makedirs(self.ts_dir)
        en_ts = os.path.join(self.ts_dir, "en.tslang")
        root = ET.Element("tslang", uid="core", lang="en")
        sec = ET.SubElement(root, "section", name="Interface")
        ET.SubElement(sec, "key", name="hello").text = "Hello World"
        tree = ET.ElementTree(root)
        tree.write(en_ts, encoding='utf-8')

    def test_01_parse_and_build_json(self):
        """Test that TranslationBuilder generates a correct JSON file"""
        builder = TranslationBuilder(self.temp_root)
        builder.build()

        en_path = os.path.join(self.temp_root, "lang", "en.json")
        self.assertTrue(os.path.exists(en_path))
        with open(en_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIn("core", data)
        self.assertEqual(data["core"]["Interface"]["hello"], "Hello World")

    def test_02_language_manager_fallback(self):
        """Test LanguageManager.get() with missing language fallback"""
        builder = TranslationBuilder(self.temp_root)
        builder.build()

        # Create a minimal extension manager mock
        class MockExtManager:
            class extensions:
                @staticmethod
                def items():
                    return [("core", {"path": self.temp_root})]

        lang_mgr = LanguageManager(self.temp_root)
        lang_mgr.extension_manager = MockExtManager()
        lang_mgr.load_translations()

        # Should return the English value
        self.assertEqual(lang_mgr.get("hello"), "Hello World")
        # Missing key returns key itself
        self.assertEqual(lang_mgr.get("missing_key"), "missing_key")

if __name__ == '__main__':
    unittest.main()