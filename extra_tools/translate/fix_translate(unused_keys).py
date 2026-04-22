import os
import re
import xml.etree.ElementTree as ET

def get_unused_keys(status_file_path: str) -> set:
    """
    Parses the translation_status.txt file to extract a set of unused keys.
    """
    unused_keys = set()
    try:
        with open(status_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"  [ERROR] Status file not found at: {status_file_path}")
        return unused_keys

    in_unused_section = False
    for line in lines:
        stripped_line = line.strip()
        if stripped_line == "--- Unused Keys in en.tslang (Defined but not used in code) ---":
            in_unused_section = True
            continue
        if in_unused_section:
            if stripped_line.startswith("---"):
                break  # End of section
            if stripped_line.startswith("- "):
                key_name = stripped_line[2:].strip()
                unused_keys.add(key_name)
    
    print(f"  [INFO] Found {len(unused_keys)} unused keys to remove.")
    return unused_keys

def find_tslang_files(root_path: str) -> list:
    """
    Finds all .tslang files within the project structure.
    """
    tslang_files = []
    scan_paths = [
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

def process_file(file_path: str, unused_keys: set):
    """
    Parses a .tslang file, removes unused keys, and saves it back.
    """
    if not unused_keys:
        return

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        keys_removed_count = 0

        # --- Process keys within <section> tags ---
        for section in root.findall('section'):
            keys_to_remove_section = [k for k in section.findall('key') if k.get('name') in unused_keys]
            for key_element in keys_to_remove_section:
                section.remove(key_element)
                keys_removed_count += 1

        # --- Process keys directly under the <tslang> root tag ---
        keys_to_remove_root = [k for k in root.findall('key') if k.get('name') in unused_keys]
        for key_element in keys_to_remove_root:
            root.remove(key_element)
            keys_removed_count += 1

        if keys_removed_count > 0:
            # Pretty-print the XML
            ET.indent(tree, space="    ")
            # Write back with XML declaration
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            print(f"    - Cleaned {os.path.basename(file_path)}: Removed {keys_removed_count} keys.")
        else:
            print(f"    - Skipped {os.path.basename(file_path)}: No unused keys found.")

    except ET.ParseError as e:
        print(f"  [ERROR] Failed to parse {file_path}: {e}")
    except Exception as e:
        print(f"  [ERROR] An unexpected error occurred with {file_path}: {e}")

def main():
    """
    Main function to orchestrate the translation file cleanup.
    """
    print("========================================")
    print("  ELAI-DevKit Translation File Cleaner")
    print("========================================")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Go one level up from 'extra_tools'
    status_file = os.path.join(project_root, 'logs', 'translation_status.txt')

    unused_keys = get_unused_keys(status_file)
    if not unused_keys:
        print("  [INFO] No unused keys listed in status file. Nothing to do.")
        return

    tslang_files = find_tslang_files(project_root)
    if not tslang_files:
        print("  [INFO] No .tslang files found.")
        return

    print("\n  Processing files...")
    for file_path in tslang_files:
        process_file(file_path, unused_keys)

    print("\n  [SUCCESS] Translation cleanup finished.")
    print("  Please re-run the translation_validator.py to confirm the changes.")


if __name__ == "__main__":
    main()