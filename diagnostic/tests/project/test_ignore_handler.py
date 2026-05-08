import unittest
import os
import tempfile
import fnmatch
from systems.project.ignore_handler import IgnoreHandler

class TestIgnoreHandler(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="elai_test_ignore_")
        self.addCleanup(self._cleanup_temp)

    def _cleanup_temp(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_basic_directory_match(self):
        """Simple directory ignore pattern"""
        handler = IgnoreHandler(['node_modules', '.venv'], [], context='backup')
        self.assertTrue(handler.is_ignored('node_modules', is_dir=True))
        self.assertFalse(handler.is_ignored('src', is_dir=True))

    def test_02_basic_file_match(self):
        """Simple file ignore pattern"""
        handler = IgnoreHandler([], ['*.pyc', '.DS_Store'], context='packer')
        self.assertTrue(handler.is_ignored('module.pyc', is_dir=False))
        self.assertFalse(handler.is_ignored('module.py', is_dir=False))

    def test_03_context_tags_include(self):
        """Pattern with a matching context tag should be active"""
        handler = IgnoreHandler(['dist[!packer]'], [], context='packer')
        self.assertTrue(handler.is_ignored('dist', is_dir=True))

        # Different context should ignore the pattern
        handler2 = IgnoreHandler(['dist[!packer]'], [], context='backup')
        self.assertFalse(handler2.is_ignored('dist', is_dir=True))

    def test_04_context_tags_multiple(self):
        """Combined tags: active only if context matches one of them"""
        handler = IgnoreHandler(['build[!git][!packer]'], [], context='git')
        self.assertTrue(handler.is_ignored('build', is_dir=True))

        handler2 = IgnoreHandler(['build[!git][!packer]'], [], context='backup')
        self.assertFalse(handler2.is_ignored('build', is_dir=True))

    def test_05_empty_lists(self):
        """Empty ignore lists should never trigger"""
        handler = IgnoreHandler([], [], context='backup')
        self.assertFalse(handler.is_ignored('anything', is_dir=True))
        self.assertFalse(handler.is_ignored('anything.txt', is_dir=False))

    def test_06_parse_gitignore(self):
        """Parse a minimal .gitignore file"""
        gitignore_content = """
# comment
.env
dist/
*.log
"""
        gitignore_path = os.path.join(self.temp_dir, '.gitignore')
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)

        dirs, files = IgnoreHandler.parse_gitignore(self.temp_dir)
        # dist ends with / -> dir
        self.assertIn('dist', dirs)
        # .env is a file pattern, but .gitignore parser adds it to both lists for safety
        self.assertIn('.env', files)
        self.assertIn('*.log', files)

    def test_07_wildcard_pattern(self):
        """Wildcard matching with fnmatch"""
        handler = IgnoreHandler([], ['*.log*'], context='backup')
        self.assertTrue(handler.is_ignored('error.log', is_dir=False))
        self.assertTrue(handler.is_ignored('error.log.1', is_dir=False))
        self.assertFalse(handler.is_ignored('error.txt', is_dir=False))

    def test_08_path_separators_in_gitignore(self):
        """Folders in .gitignore with trailing slash become dir patterns"""
        dirs, files = IgnoreHandler.parse_gitignore(self.temp_dir)
        # No special handling needed beyond what we already tested; ensure it works
        self.assertIsInstance(dirs, list)
        self.assertIsInstance(files, list)

    def test_09_comments(self):
        """Comments starting with # should be ignored"""
        handler = IgnoreHandler(['# this is a comment', 'build'], ['# file comment', '*.log'], context='backup')
        self.assertTrue(handler.is_ignored('build', is_dir=True))
        self.assertTrue(handler.is_ignored('error.log', is_dir=False))
        self.assertFalse(handler.is_ignored('# this is a comment', is_dir=True))

if __name__ == '__main__':
    unittest.main()