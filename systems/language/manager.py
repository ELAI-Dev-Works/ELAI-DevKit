import json
import os
import inspect
from typing import Dict, List, Optional

class LanguageManager:
    def __init__(self, app_root_path: str):
        self.app_root_path = app_root_path
        self.lang_dir = os.path.join(self.app_root_path, 'lang')
        self.translations: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}
        # Structure: {lang_code: {uid: {section: {key: value}}}}
        
        self.current_language = 'en'
        self.extension_manager = None
        
        # Rebuild translations from .tslang sources (like DocBuilder)
        self.rebuild_translations()
        
        # Load JSON files
        self.load_translations()

    def rebuild_translations(self):
        """Regenerates JSON files from .tslang sources on startup"""
        from .builder import TranslationBuilder
        try:
            builder = TranslationBuilder(self.app_root_path)
            builder.build()
        except Exception as e:
            print(f"[LanguageManager] Error rebuilding translations: {e}")

    def load_translations(self):
        """Loads JSON translation files from lang/ directory"""
        if not os.path.isdir(self.lang_dir):
            return
        
        for lang_file in os.listdir(self.lang_dir):
            if lang_file.endswith('.json'):
                lang_code = lang_file[:-5]  # Remove .json extension
                file_path = os.path.join(self.lang_dir, lang_file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"[LanguageManager] Error loading {lang_file}: {e}")

    def load_extension_languages(self, extension_manager):
        """
        Stores reference to extension manager for uid detection.
        Translations are already loaded via rebuild_translations().
        """
        self.extension_manager = extension_manager

    def get_available_languages(self) -> List[str]:
        """Returns a list of loaded language codes"""
        return sorted(self.translations.keys())

    def set_language(self, lang_code: str):
        """Sets the current language for the application"""
        if lang_code in self.translations:
            self.current_language = lang_code
        else:
            print(f"[LanguageManager] Warning: Language '{lang_code}' not found. Using 'en'.")
            self.current_language = 'en'

    def _detect_uid_from_caller(self) -> str:
        """
        Automatically detects uid by inspecting call stack.
        Matches caller's file path against extension metadata.
        
        Returns:
            Extension uid (e.g., 'dev_patcher') or 'core' if not found
        """
        if not self.extension_manager:
            return 'core'
        
        # Inspect call stack to find caller's file path
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the actual caller (skip get() itself)
            caller_frame = frame.f_back.f_back
            if caller_frame:
                caller_file = caller_frame.f_code.co_filename
                
                # Normalize path for comparison
                caller_file = os.path.normpath(caller_file)
                
                # Check if caller is from an extension
                for name, meta in self.extension_manager.extensions.items():
                    ext_path = os.path.normpath(meta['path'])
                    if caller_file.startswith(ext_path):
                        return name
        finally:
            del frame
        
        # Default to 'core' if not found
        return 'core'

    def get(self, key: str, section: str = 'strings') -> str:
        """
        Gets a translated string for a given key.
        
        Args:
            key: Translation key
            section: Section name (kept for backward compatibility, searches all sections)
        
        Returns:
            Translated string, or key itself if not found
        
        Fallback order:
            1. Current language + detected uid
            2. Current language + all other uids
            3. English + detected uid
            4. English + all other uids
            5. Key itself
        """
        # Auto-detect uid from caller
        detected_uid = self._detect_uid_from_caller()
        
        # Try current language with detected uid
        value = self._search_key(self.current_language, detected_uid, key)
        if value is not None:
            return value
        
        # Fallback: search in all other uids for current language
        value = self._search_key_in_all_uids(self.current_language, key, exclude_uid=detected_uid)
        if value is not None:
            return value
        
        # Fallback to English with detected uid
        if self.current_language != 'en':
            value = self._search_key('en', detected_uid, key)
            if value is not None:
                return value
            
            # Fallback: search in all other uids for English
            value = self._search_key_in_all_uids('en', key, exclude_uid=detected_uid)
            if value is not None:
                return value
        
        # Fallback to key itself
        return key

    def _search_key(self, lang: str, uid: str, key: str) -> Optional[str]:
        """
        Searches for key in all sections of given lang/uid.
        
        Args:
            lang: Language code
            uid: Extension uid
            key: Translation key
        
        Returns:
            Translation value or None if not found
        """
        try:
            uid_data = self.translations[lang][uid]
            # Search in all sections
            for section_name, section_data in uid_data.items():
                if key in section_data:
                    return section_data[key]
        except KeyError:
            pass
        
        return None

    def _search_key_in_all_uids(self, lang: str, key: str, exclude_uid: str = None) -> Optional[str]:
        """
        Searches for key across all uids, excluding specified uid.
        
        Args:
            lang: Language code
            key: Translation key
            exclude_uid: UID to exclude from search
        
        Returns:
            Translation value or None if not found
        """
        if lang not in self.translations:
            return None
        
        for uid, uid_data in self.translations[lang].items():
            if uid == exclude_uid:
                continue
            for section_name, section_data in uid_data.items():
                if key in section_data:
                    return section_data[key]
        
        return None