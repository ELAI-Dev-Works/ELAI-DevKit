import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Make sure root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from systems.gui.themes.manager import ThemeManager

class TestThemeManager(unittest.TestCase):
    def setUp(self):
        # Mock MainWindow
        self.mw = MagicMock()
        self.mw.root_path = None
        self.mw.path_label = MagicMock()
        
    def test_available_schemes_and_themes(self):
        tm = ThemeManager(self.mw)
        colors = tm.get_available_color_schemes()
        themes = tm.get_available_themes()
        self.assertIn('dark', colors)
        self.assertIn('light', colors)
        self.assertIn('ocean', colors)
        self.assertIn('basic', themes)
        self.assertIn('clean', themes)
        self.assertIn('sleek', themes)

    @patch('systems.gui.themes.manager.importlib.import_module')
    def test_apply_theme_success(self, mock_import):
        mock_color_module = MagicMock()
        mock_color_module.palette = {"background": "#000", "text": "#fff"}
        mock_style_module = MagicMock()
        mock_style_module.get_stylesheet.return_value = "/* test */"
        mock_import.side_effect = lambda name: mock_color_module if 'color' in name else mock_style_module

        tm = ThemeManager(self.mw)
        tm.apply_theme('dark', 'clean')
        self.assertEqual(tm.current_color_scheme, 'dark')
        self.assertEqual(tm.current_theme, 'clean')
        mock_import.assert_called()
        # Should update path label style
        self.mw.path_label.setStyleSheet.assert_called()

    def test_invalid_theme_fallback(self):
        tm = ThemeManager(self.mw)
        # Should not crash, but internally fallbacks to dark/clean
        tm.apply_theme('nonexistent', 'invalid')
        # After fallback, should still have a valid palette
        self.assertTrue(tm.current_palette)

if __name__ == '__main__':
    unittest.main()