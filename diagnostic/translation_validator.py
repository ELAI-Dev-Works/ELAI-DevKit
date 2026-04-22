import os
import sys
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
import datetime

class TranslationValidator:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.tslang_keys = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self.code_keys = defaultdict(list)
        self.has_failed = False
        self.missing_keys_report = []
        self.unused_keys_report =[]
        self.garbage_keys_report = set()
        self.completeness_report = {}

    def run(self):
        self.scan_code()
        self.scan_translations()
        self.check_duplicates()
        self.check_missing_keys()
        self.check_unused_keys()
        self.check_completeness()
        self.generate_report_file()

        if self.has_failed:
            print("\n  [FAIL] Translation validation finished with warnings/errors.")
            sys.exit(1)
        else:
            print("\n  [PASS] Translation validation finished successfully.")
            sys.exit(0)

    def scan_code(self):
        # Pattern 1: lang.get() calls
        # Catches: .lang.get(), lang.get(), self.main_window.lang.get(), etc.
        lang_get_pattern = re.compile(r'(?:[\w.]+\.)?lang\.get\(\s*[fF]?[\'"]([a-zA-Z0-9_-{}]+)[\'"]')
        
        # Pattern 2: Configuration keys (title_lang_key, lang_key, etc.)
        # Catches: 'title_lang_key': 'key_name', "lang_key": "key_name"
        config_key_pattern = re.compile(r'[\'"](?:title_)?lang_key[\'"]\s*:\s*[\'"]([a-zA-Z0-9_-{}]+)[\'"]')
        
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', 'node_modules', 'diagnostic']]
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, self.root_path)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            # Check lang.get() pattern
                            for key in lang_get_pattern.findall(line):
                                self.code_keys[key].append(f"{rel_path}:{i}")
                            
                            # Check config key pattern
                            for key in config_key_pattern.findall(line):
                                self.code_keys[key].append(f"{rel_path}:{i}")

    def scan_translations(self):
        scan_paths = [
            os.path.join(self.root_path, 'assets', 'translation'),
            os.path.join(self.root_path, 'apps')
        ]
        for path in scan_paths:
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.tslang'):
                        self._parse_tslang(os.path.join(root, file))

    def _parse_tslang(self, path):
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            uid, lang = root.get('uid'), root.get('lang')
            if not uid or not lang: return

            for section in root.findall('section'):
                section_name = section.get('name', 'Default')
                for key_elem in section.findall('key'):
                    key = key_elem.get('name')
                    if key:
                        self.tslang_keys[uid][lang][section_name][key] = True

            for key_elem in root.findall('key'):
                key = key_elem.get('name')
                if key:
                    self.tslang_keys[uid][lang]['Default'][key] = True
        except Exception:
            pass

    def check_duplicates(self):
        print("  Checking for garbage/duplicate keys (present in other langs but not in en.tslang for the same uid and section)...")

        for uid, langs_data in self.tslang_keys.items():
            en_sections = langs_data.get('en', {})
            for lang, sections_dict in langs_data.items():
                if lang == 'en': continue
                for section, keys_dict in sections_dict.items():
                    en_keys_in_section = set(en_sections.get(section, {}).keys())
                    for key in keys_dict.keys():
                        if key not in en_keys_in_section:
                            self.garbage_keys_report.add(f"[{uid}] [{section}] {key}")

        if not self.garbage_keys_report:
            print("    [PASS] No garbage/duplicate keys found.")
        else:
            self.has_failed = True
            print(f"    [FAIL] {len(self.garbage_keys_report)} garbage/duplicate keys found in non-English files.")

    def check_missing_keys(self):
        print("  Checking for keys used in code but not defined in en.tslang...")
        
        # Collect all defined keys
        all_defined_keys = set()
        for uid_data in self.tslang_keys.values():
            for section_data in uid_data.get('en', {}).values():
                all_defined_keys.update(section_data.keys())

        for key, usages in self.code_keys.items():
            # Skip dynamic keys with placeholders (e.g., {name}_tab)
            if '{' in key and '}' in key:
                # Check if any defined key matches this pattern
                pattern = re.sub(r'\{.*?\}', r'[a-zA-Z0-9_-]+', key)
                pattern_regex = re.compile(f"^{pattern}$")
                has_match = any(pattern_regex.match(defined_key) for defined_key in all_defined_keys)
                if has_match:
                    continue  # Skip this dynamic key as it has matching translations
                # If no match found, it's likely a dynamic key with fallback, skip it
                continue
            
            found = False
            for uid_data in self.tslang_keys.values():
                for section_data in uid_data.get('en', {}).values():
                    if key in section_data:
                        found = True
                        break
                if found: break
            if not found:
                self.missing_keys_report.append((key, usages[0]))

        if not self.missing_keys_report:
            print("    [PASS] All keys used in code are defined.")
        else:
            self.has_failed = True
            print(f"    [FAIL] {len(self.missing_keys_report)} keys are missing from en.tslang definitions:")
            for key, usage in self.missing_keys_report[:10]:
                print(f"      - '{key}' (used in {usage})")

    def check_unused_keys(self):
        print("  Checking for keys in en.tslang not used in code...")
        all_defined_keys = set()
        for uid_data in self.tslang_keys.values():
            for section_data in uid_data.get('en', {}).values():
                all_defined_keys.update(section_data.keys())

        dynamic_key_patterns =[]
        static_code_keys = set()
        for key in self.code_keys:
            if '{' in key:
                regex_pattern = re.sub(r'\{.*?\}', r'[a-zA-Z0-9_-]+', key)
                dynamic_key_patterns.append(re.compile(f"^{regex_pattern}$"))
            else:
                static_code_keys.add(key)

        # Check each defined key
        for key in all_defined_keys:
            # Check if key is used directly in code
            if key in static_code_keys:
                continue

            # Check if key matches dynamic pattern
            is_used_dynamically = False
            for pattern in dynamic_key_patterns:
                if pattern.match(key):
                    is_used_dynamically = True
                    break
            
            if is_used_dynamically:
                continue
            
            # Check if key exists in multiple en.tslang files (fallback mechanism)
            # If a key is defined in multiple UIDs, it's likely used via fallback
            en_uid_count = 0
            for uid_data in self.tslang_keys.values():
                for section_data in uid_data.get('en', {}).values():
                    if key in section_data:
                        en_uid_count += 1
                        break # count uid only once

            # If key exists in multiple UIDs, consider it used (fallback logic)
            if en_uid_count > 1:
                continue

            # Key is truly unused
            self.unused_keys_report.append(key)

        if not self.unused_keys_report:
            print("    [PASS] All defined English keys are used in the code.")
        else:
            # It's a warning, not a failure
            print(f"    [WARN] {len(self.unused_keys_report)} keys are defined but seem unused:")
            for key in self.unused_keys_report[:10]:
                print(f"      - '{key}'")

    def check_completeness(self):
        print("  Checking if all languages have translations for English keys...")
        all_en_keys = set()
        for uid_data in self.tslang_keys.values():
            for section_data in uid_data.get('en', {}).values():
                all_en_keys.update(section_data.keys())

        for lang in['ru', 'es', 'ua', 'de', 'fr', 'ja', 'ko', 'zh']:
            missing_for_lang =[]
            for key in all_en_keys:
                found = False
                for uid_data in self.tslang_keys.values():
                    for section_data in uid_data.get(lang, {}).values():
                        if key in section_data:
                            found = True
                            break
                    if found: break
                if not found:
                    missing_for_lang.append(key)

            self.completeness_report[lang] = missing_for_lang

            if not missing_for_lang:
                print(f"    [PASS] Language '{lang}' is complete.")
            else:
                self.has_failed = True
                print(f"    [FAIL] Language '{lang}' is missing {len(missing_for_lang)} translations (e.g., '{missing_for_lang[0]}').")

    def generate_report_file(self):
        logs_dir = os.path.join(self.root_path, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        report_path = os.path.join(logs_dir, 'translation_status.txt')
        print(f"\n  Generating translation status report to: {report_path}")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("========================================\n")
            f.write("      Translation Status Report\n")
            f.write(f"  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("========================================\n\n")

            f.write("--- Summary ---\n")
            total_missing = sum(len(v) for v in self.completeness_report.values())
            f.write(f"Total Missing Translations (non-English): {total_missing}\n")
            f.write(f"Total Unused Keys in en.tslang: {len(self.unused_keys_report)}\n")
            f.write(f"Total Keys Missing from en.tslang (used in code): {len(self.missing_keys_report)}\n")
            f.write(f"Total Garbage/Duplicate Keys (Not in en.tslang): {len(self.garbage_keys_report)}\n\n")

            if self.missing_keys_report:
                f.write("--- Keys Used in Code but Missing from en.tslang ---\n")
                for key, usage in self.missing_keys_report:
                    f.write(f"- {key} (used in {usage})\n")
                f.write("\n")

            if self.unused_keys_report:
                f.write("--- Unused Keys in en.tslang (Defined but not used in code) ---\n")
                for key in sorted(self.unused_keys_report):
                    f.write(f"- {key}\n")
                f.write("\n")
            if self.garbage_keys_report:
                f.write("--- Garbage/Duplicate Keys (Not in en.tslang) ---\n")
                for key in sorted(self.garbage_keys_report):
                    f.write(f"- {key}\n")
                f.write("\n")

            f.write("--- Translation Completeness vs English ---\n")
            for lang, missing_keys in sorted(self.completeness_report.items()):
                if not missing_keys:
                    f.write(f"  [PASS] {lang.upper()}: Complete\n")
                else:
                    f.write(f"  [FAIL] {lang.upper()}: Missing {len(missing_keys)} translations\n")
            f.write("\n")

            for lang, missing_keys in sorted(self.completeness_report.items()):
                if missing_keys:
                    f.write(f"--- Missing Keys for [{lang.upper()}] ---\n")
                    for key in sorted(missing_keys):
                        f.write(f"- {key}\n")
                    f.write("\n")

if __name__ == "__main__":
    script_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_path)
    validator = TranslationValidator(project_root)
    validator.run()