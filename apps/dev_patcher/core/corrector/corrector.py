from .analyze import Analyzer

class PatchCorrector:
    """
    Analyzes raw patch text for syntax errors and suggests corrections.
    """
    def __init__(self, patch_text: str, experimental_flags: dict, lang_manager):
        self.patch_text = patch_text
        self.flags = experimental_flags or {}
        self.lang = lang_manager
        self.issues =[]
        self.analyzer = Analyzer(self.patch_text, self.flags, self.lang)

    def analyze(self):
        """
        Runs all checks and returns a list of found issues.
        """
        self.issues = self.analyzer.run()
        return self.issues