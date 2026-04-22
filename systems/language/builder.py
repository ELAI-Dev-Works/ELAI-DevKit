import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, List

class TranslationBuilder:
    """
    Builds JSON translation files from .tslang XML sources.
    Similar to DocBuilder - runs on application startup.
    """
    
    def __init__(self, app_root_path: str):
        self.app_root_path = app_root_path
        self.lang_dir = os.path.join(app_root_path, 'lang')
        self.translations: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}
        # Structure: {lang_code: {uid: {section: {key: value}}}}
    
    def build(self):
        """Main entry point: scans all .tslang files and generates JSON files"""
        print("[TranslationBuilder] Starting translation build...")
        
        # Scan and parse all .tslang files
        tslang_files = self._scan_tslang_files()
        
        if not tslang_files:
            print("[TranslationBuilder] Warning: No .tslang files found!")
            return
        
        print(f"[TranslationBuilder] Found {len(tslang_files)} .tslang files")
        
        # Parse each .tslang file
        for tslang_file in tslang_files:
            try:
                self._parse_tslang(tslang_file)
            except Exception as e:
                print(f"[TranslationBuilder] Error parsing {tslang_file}: {e}")
        
        # Validate English translations exist
        self._validate_english()
        
        # Write JSON files
        self._write_json_files()
        
        print("[TranslationBuilder] Build complete!")
    
    def _scan_tslang_files(self) -> List[str]:
        """
        Scans for .tslang files in:
        - assets/translation/
        - apps/*/assets/translation/

        Returns:
            List of absolute paths to .tslang files
        """
        tslang_files = []
        
        # Scan assets/translation/
        core_translation_dir = os.path.join(self.app_root_path, 'assets', 'translation')
        if os.path.isdir(core_translation_dir):
            for filename in os.listdir(core_translation_dir):
                if filename.endswith('.tslang'):
                    tslang_files.append(os.path.join(core_translation_dir, filename))

        # Scan apps/*/assets/translation/
        apps_dir = os.path.join(self.app_root_path, 'apps')
        if os.path.isdir(apps_dir):
            for app_name in os.listdir(apps_dir):
                app_translation_dir = os.path.join(apps_dir, app_name, 'assets', 'translation')
                if os.path.isdir(app_translation_dir):
                    for filename in os.listdir(app_translation_dir):
                        if filename.endswith('.tslang'):
                            tslang_files.append(os.path.join(app_translation_dir, filename))
        
        return tslang_files
    
    def _parse_tslang(self, file_path: str):
        """
        Parses a .tslang XML file and merges into translations dict.
        
        Args:
            file_path: Path to .tslang file
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract uid and lang from root attributes
            uid = root.get('uid')
            lang = root.get('lang')
            
            if not uid or not lang:
                print(f"[TranslationBuilder] Warning: Missing uid or lang in {file_path}")
                return
            
            # Initialize structure if needed
            if lang not in self.translations:
                self.translations[lang] = {}
            if uid not in self.translations[lang]:
                self.translations[lang][uid] = {}
            
            # Parse sections and keys
            for section_elem in root.findall('section'):
                section_name = section_elem.get('name', 'Default')
                
                if section_name not in self.translations[lang][uid]:
                    self.translations[lang][uid][section_name] = {}
                
                # Parse keys in this section
                for key_elem in section_elem.findall('key'):
                    key_name = key_elem.get('name')
                    key_value = key_elem.text or ''
                    
                    if key_name:
                        self.translations[lang][uid][section_name][key_name] = key_value
            
            # Handle keys without sections (direct children of root)
            for key_elem in root.findall('key'):
                key_name = key_elem.get('name')
                key_value = key_elem.text or ''
                
                if key_name:
                    if 'Default' not in self.translations[lang][uid]:
                        self.translations[lang][uid]['Default'] = {}
                    self.translations[lang][uid]['Default'][key_name] = key_value
        
        except ET.ParseError as e:
            print(f"[TranslationBuilder] XML parse error in {file_path}: {e}")
        except Exception as e:
            print(f"[TranslationBuilder] Error parsing {file_path}: {e}")
    
    def _validate_english(self):
        """
        Validates that English translations exist for all UIDs.
        Prints warnings for missing English translations.
        """
        if 'en' not in self.translations:
            print("[TranslationBuilder] WARNING: No English translations found!")
            return
        
        # Collect all UIDs from all languages
        all_uids = set()
        for lang_data in self.translations.values():
            all_uids.update(lang_data.keys())
        
        # Check if English exists for each UID
        english_uids = set(self.translations['en'].keys())
        missing_uids = all_uids - english_uids
        
        if missing_uids:
            print(f"[TranslationBuilder] WARNING: Missing English translations for UIDs: {missing_uids}")
    
    def _write_json_files(self):
        """
        Writes JSON files to lang/ directory.
        One file per language: lang/en.json, lang/ru.json, etc.
        """
        # Create lang directory if it doesn't exist
        os.makedirs(self.lang_dir, exist_ok=True)
        
        # Write each language to a separate JSON file
        for lang_code, lang_data in self.translations.items():
            output_file = os.path.join(self.lang_dir, f'{lang_code}.json')
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(lang_data, f, ensure_ascii=False, indent=2)
                
                # Count total keys for this language
                total_keys = sum(
                    len(section_data)
                    for uid_data in lang_data.values()
                    for section_data in uid_data.values()
                )
                
                print(f"[TranslationBuilder] Created {output_file} ({total_keys} keys)")
            
            except Exception as e:
                print(f"[TranslationBuilder] Error writing {output_file}: {e}")


if __name__ == '__main__':
    # For testing: run builder directly
    import sys

    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        # Assume running from systems/language/
        root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print(f"[TranslationBuilder] Root path: {root_path}")
    
    builder = TranslationBuilder(root_path)
    builder.build()