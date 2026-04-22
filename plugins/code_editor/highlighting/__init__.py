from .python import PythonHighlighter
from .javascript import JavascriptHighlighter
from .html import HTMLHighlighter
from .css import CSSHighlighter
from .json_hl import JSONHighlighter

class HighlighterManager:
    """Factory class to provide syntax highlighters based on language name."""
    @staticmethod
    def get_highlighter(language: str, document=None):
        language = language.lower()
        if language in['python', 'py']:
            return PythonHighlighter(document)
        elif language in['javascript', 'js', 'typescript', 'ts', 'node', 'nodejs']:
            return JavascriptHighlighter(document)
        elif language in['html', 'htm', 'html5']:
            return HTMLHighlighter(document)
        elif language in['css', 'scss', 'sass']:
            return CSSHighlighter(document)
        elif language in['json']:
            return JSONHighlighter(document)
        return None