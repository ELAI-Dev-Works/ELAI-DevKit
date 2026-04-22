import fnmatch
import os
import re
from typing import List, Set

class IgnoreHandler:
    """
    A centralized handler to check whether a file or folder should be ignored.
    Supports simple names, wildcards, and context tags (e.g. 'node_modules [!packer]').
    """
    def __init__(self, ignore_dirs: List[str], ignore_files: List[str], context: str = None):
        self.context = context
        self.ignore_dir_patterns: Set[str] = self._parse_patterns(ignore_dirs)
        self.ignore_file_patterns: Set[str] = self._parse_patterns(ignore_files)

    def _parse_patterns(self, patterns: List[str]) -> Set[str]:
        active = set()
        for p in patterns:
            p = p.strip()
            if not p: continue
            tags = re.findall(r'\[!([a-zA-Z0-9_]+)\]', p)
            clean_p = re.sub(r'\s*\[![a-zA-Z0-9_]+\]', '', p).strip()

            if not tags or (self.context and self.context in tags):
                active.add(clean_p)
        return active

    def is_ignored(self, name: str, is_dir: bool) -> bool:
        """
        Checks whether the name of the file or folder matches any template.
        :param name: The name of the file or folder to verify (not the full path).
        :param is_dir: True if the folder is checked, False if the file.
        :return: True, if the element is to be ignored.
        """
        patterns = self.ignore_dir_patterns if is_dir else self.ignore_file_patterns

        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    @staticmethod
    def parse_gitignore(root_path: str) -> (List[str], List[str]):
        """
        Parses the .gitignore file in the root_path and returns lists of ignored dirs and files.
        This is a basic implementation mapping .gitignore logic to simple fnmatch patterns.
        """
        dirs, files = [], []
        gitignore_path = os.path.join(root_path, '.gitignore')

        if not os.path.exists(gitignore_path):
            return [], []

        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Basic conversion logic
                    # If it ends with /, it's definitely a directory
                    if line.endswith('/'):
                        dirs.append(line.rstrip('/'))
                    else:
                        # Otherwise, add to both to be safe (or just files, but folder matches are common without trailing slash)
                        # In .gitignore 'node_modules' matches the folder.
                        # In fnmatch, we need it in ignore_dir_patterns to match a directory check.
                        files.append(line)
                        dirs.append(line)
        except Exception:
            pass # Fail silently on read error

        return dirs, files