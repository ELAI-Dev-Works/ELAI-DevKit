import os
import xml.etree.ElementTree as ET

def get_duplicate_keys(status_file_path: str) -> dict:
    """
    Parses the translation_status.txt file to extract a dict of duplicate/garbage keys.
    Returns: dict mapping uid to a dict of sections containing a set of key names.
    """
    duplicate_keys = {}
    try:
        with open(status_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"  [ERROR] Status file not found at: {status_file_path}")
        return duplicate_keys

    in_duplicate_section = False
    for line in lines:
        stripped_line = line.strip()
        if stripped_line == "--- Garbage/Duplicate Keys (Not in en.tslang) ---":
            in_duplicate_section = True
            continue
        if in_duplicate_section:
            if stripped_line.startswith("---"):
                break  # End of section
            if stripped_line.startswith("- "):
                content = stripped_line[2:].strip()
                # Parse format: [uid] [section] key_name
                if content.startswith('[') and '] [' in content:
                    uid_part, rest = content.split('] [')
                    uid = uid_part[1:].strip()
                    if '] ' in rest:
                        section_part, key = rest.split('] ', 1)
                        section = section_part.strip()
                        key = key.strip()
                        
                        if uid not in duplicate_keys:
                            duplicate_keys[uid] = {}
                        if section not in duplicate_keys[uid]:
                            duplicate_keys[uid][section] = set()
                        duplicate_keys[uid][section].add(key)

    total_keys = sum(len(keys) for uid_dict in duplicate_keys.values() for keys in uid_dict.values())
    print(f"  [INFO] Found {total_keys} duplicate/garbage keys to remove.")
    return duplicate_keys

def find_tslang_files(root_path: str) -> list:
    """
    Finds all .tslang files within the project structure.
    """
    tslang_files = []
    scan_paths =[
        os.path.join(root_path, 'assets', 'translation'),
        os.path.join(root_path, 'apps')
    ]
    for path in scan_paths:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.tslang'):
                    tslang_files.append(os.path.join(root, file))
    print(f"  [INFO] Found {len(tslang_files)} .tslang files to process.")
    return tslang_files

def process_file(file_path: str, duplicate_keys: dict):
    """
    Parses a .tslang file, removes duplicate keys matching its UID and Section, and saves it back.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        uid = root.get('uid')
        lang = root.get('lang')

        keys_removed_count = 0

        # Check for intra-file duplicates if it's an English file
        if lang == 'en':
            seen_keys = set()
            for section in root.findall('.//section'):
                for key_element in list(section.findall('key')):
                    key_name = key_element.get('name')
                    if (section.get('name'), key_name) in seen_keys:
                        section.remove(key_element)
                        keys_removed_count += 1
                    else:
                        seen_keys.add((section.get('name'), key_name))

        if not uid or uid not in duplicate_keys:
            if keys_removed_count > 0:
                if hasattr(ET, "indent"):
                    ET.indent(tree, space="    ")
                tree.write(file_path, encoding='utf-8', xml_declaration=True)
                print(f"    - Cleaned {os.path.basename(file_path)}: Removed {keys_removed_count} intra-file duplicate keys.")
            return

        keys_to_remove_dict = duplicate_keys[uid]

        # --- Process keys within <section> tags ---
        for section in root.findall('section'):
            sec_name = section.get('name', 'Default')
            if sec_name in keys_to_remove_dict:
                keys_to_remove_set = keys_to_remove_dict[sec_name]
                keys_to_remove_elements =[k for k in section.findall('key') if k.get('name') in keys_to_remove_set]
                for key_element in keys_to_remove_elements:
                    section.remove(key_element)
                    keys_removed_count += 1

            # If section becomes empty after removals, remove it
            if not section.findall('key'):
                root.remove(section)

        # --- Process keys directly under the <tslang> root tag ---
        if 'Default' in keys_to_remove_dict:
            keys_to_remove_set = keys_to_remove_dict['Default']
            keys_to_remove_root =[k for k in root.findall('key') if k.get('name') in keys_to_remove_set]
            for key_element in keys_to_remove_root:
                root.remove(key_element)
                keys_removed_count += 1

        if keys_removed_count > 0:
            # Pretty-print the XML
            if hasattr(ET, "indent"):
                ET.indent(tree, space="    ")
            # Write back with XML declaration
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            print(f"    - Cleaned {os.path.basename(file_path)}: Removed {keys_removed_count} keys.")

    except ET.ParseError as e:
        print(f"  [ERROR] Failed to parse {file_path}: {e}")
    except Exception as e:
        print(f"  [ERROR] An unexpected error occurred with {file_path}: {e}")

def main():
    """
    Main function to orchestrate the translation file cleanup.
    """
    print("========================================")
    print("  ELAI-DevKit Translation Cleaner (Duplicates)")
    print("========================================")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir)) # Go up from extra_tools/translate
    status_file = os.path.join(project_root, 'logs', 'translation_status.txt')

    duplicate_keys = get_duplicate_keys(status_file)
    if not duplicate_keys:
        print("  [INFO] No duplicate keys listed in status file. Nothing to do.")
        return

    tslang_files = find_tslang_files(project_root)
    if not tslang_files:
        print("  [INFO] No .tslang files found.")
        return

    print("\n  Processing files...")
    for file_path in tslang_files:
        process_file(file_path, duplicate_keys)

    print("\n[SUCCESS] Translation cleanup finished.")
    print("  Please re-run the translation_validator.py to confirm the changes.")

if __name__ == "__main__":
    main()