import unittest
from unittest.mock import MagicMock
from systems.gui.utils.markdown_styler import MarkdownStyler

class TestMarkdownStyler(unittest.TestCase):
    def setUp(self):
        tm = MagicMock()
        tm.current_color_scheme = 'dark'
        tm.current_theme = 'sleek'
        type(tm).current_palette = MagicMock()
        self.styler = MarkdownStyler(tm)

    def test_header_anchor_generation(self):
        md = "# Hello\nSome text\n## Section\nMore text"
        html, css, toc = self.styler.render(md)
        self.assertIn('<a name="header-0"></a>', html)
        self.assertIn('<a name="header-1"></a>', html)
        self.assertEqual(len(toc), 2)
        self.assertEqual(toc[0], (1, 'Hello', 'header-0'))
        self.assertEqual(toc[1], (2, 'Section', 'header-1'))

    def test_code_block_extraction(self):
        md = "```python\nprint('hi')\n```"
        html, _, _ = self.styler.render(md)
        # The internal marker must not appear in the final output
        self.assertNotIn('MERKBLOCK0MERK', html)
        # The rendered HTML must contain the copy-code link
        self.assertIn('COPY CODE', html)
        self.assertIn('action:copy_0', html)

if __name__ == '__main__':
    unittest.main()