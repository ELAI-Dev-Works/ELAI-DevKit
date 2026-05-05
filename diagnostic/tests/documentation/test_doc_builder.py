import unittest
import os
import tempfile
import shutil
from systems.documentation.builder import DocBuilder

class TestDocBuilder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="elai_doc_")
        self.root = self.temp_dir
        self.apps = os.path.join(self.root, "apps", "dev_patcher")
        self.doc = os.path.join(self.apps, "doc")
        self.categories = os.path.join(self.doc, "categories")
        os.makedirs(self.categories)
        self.builder = DocBuilder(self.root)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_parse_metadata(self):
        meta_file = os.path.join(self.apps, "core", "commands", "test.cdoc")
        os.makedirs(os.path.dirname(meta_file), exist_ok=True)
        with open(meta_file, 'w', encoding='utf-8') as f:
            f.write("number = 5\ntype = command(base)\n<lang[en]>\n<md>\nHello Markdown\n</md>")
        data = self.builder._parse_doc_file(meta_file)
        self.assertEqual(data['meta']['number'], '5')
        self.assertIn("Hello Markdown", data['content'])

    def test_02_get_number_default(self):
        meta = {"number": "999"}
        self.assertEqual(self.builder._get_number(meta), 999)
        meta2 = {"number": "#"}
        self.assertEqual(self.builder._get_number(meta2), 10000)

if __name__ == '__main__':
    unittest.main()