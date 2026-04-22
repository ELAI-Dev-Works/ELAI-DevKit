import sys
import os
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QCheckBox, QSpinBox, QTextEdit, QSplitter, QGroupBox, QFormLayout,
    QDialog, QDialogButtonBox, QMessageBox
)
from PySide6.QtGui import QColor

from PySide6.QtCore import Qt, QThread, Signal

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

class ConflictDialog(QDialog):
    def __init__(self, conflicts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Translation Conflicts")
        self.setMinimumSize(700, 500)
        self.conflicts = conflicts
        self.selected_to_overwrite =[]

        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("The following keys already exist and have text. Select to OVERWRITE:"))
        self.toggle_all_btn = QPushButton("Un/Select All")
        self.toggle_all_btn.clicked.connect(self._toggle_all)
        header_layout.addWidget(self.toggle_all_btn)
        layout.addLayout(header_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Key / Language", "Current Text", "New Translation"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 200)

        # Group conflicts by key
        grouped_conflicts = defaultdict(list)
        for i, conflict in enumerate(self.conflicts):
            key_id = f"[{conflict['uid']}] {conflict['section']} -> {conflict['key']}"
            grouped_conflicts[key_id].append((i, conflict))

        for key_id, items in grouped_conflicts.items():
            parent_item = QTreeWidgetItem([key_id, "", ""])
            # Parent item is not checkable to keep logic simple, but we expand it
            self.tree.addTopLevelItem(parent_item)

            for idx, conflict in items:
                child_item = QTreeWidgetItem([conflict['lang'].upper(), conflict['existing_text'], conflict['text']])
                child_item.setFlags(child_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.CheckState.Unchecked)
                child_item.setData(0, Qt.ItemDataRole.UserRole, idx)
                parent_item.addChild(child_item)

            parent_item.setExpanded(True)

        layout.addWidget(self.tree)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _toggle_all(self):
        # Determine target state based on the first checkable child we find
        target_state = Qt.CheckState.Checked
        found_first = False

        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if parent.childCount() > 0:
                first_child = parent.child(0)
                if not found_first:
                    target_state = Qt.CheckState.Unchecked if first_child.checkState(0) == Qt.CheckState.Checked else Qt.CheckState.Checked
                    found_first = True

                for j in range(parent.childCount()):
                    parent.child(j).setCheckState(0, target_state)

    def get_overwrites(self):
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.CheckState.Checked:
                    idx = child.data(0, Qt.ItemDataRole.UserRole)
                    self.selected_to_overwrite.append(self.conflicts[idx])
        return self.selected_to_overwrite

class TranslatorWorker(QThread):
    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, api_url, api_key, model, keys, target_langs):
        super().__init__()
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.keys = keys
        self.target_langs = target_langs

    def run(self):
        try:
            batch_dict = {item['key']: item['text'] for item in self.keys}
            prompt = f"""You are a professional software localizer. Translate the following English UI texts into the requested languages: {', '.join(self.target_langs)}.
Provide the result STRICTLY as a JSON object matching this exact schema:
{{
    "lang": {{
        "<language_code>": {{
            "<key_name>": "<translated_text>"
        }}
    }}
}}
Only use the requested language codes. Do not include any other text, markdown formatting, or explanations.

Keys to translate (English):
{json.dumps(batch_dict, indent=2, ensure_ascii=False)}
"""
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {
                "model": self.model,
                "messages":[{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "stream": False
            }
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=240)
            if not response.ok:
                raise ValueError(f"API returned status {response.status_code}: {response.text}")

            response.encoding = 'utf-8'
            try:
                if response.text.strip().startswith("data:"):
                    full_content = ""
                    for line in response.text.splitlines():
                        if line.startswith("data: ") and line.strip() != "data: [DONE]":
                            try:
                                chunk = json.loads(line[6:])
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta:
                                    full_content += delta["content"]
                            except Exception:
                                pass
                    resp_data = {"choices":[{"message": {"content": full_content}}]}
                else:
                    resp_data = response.json()
            except Exception as e:
                raise ValueError(f"Failed to parse JSON response. Raw text:\n{response.text}") from e
            if "choices" not in resp_data:
                raise ValueError(f"Unexpected API response: {resp_data}")

            content = resp_data["choices"][0]["message"]["content"].strip()
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            content = content.strip()

            parsed_json = json.loads(content)
            if "lang" not in parsed_json: raise ValueError("Missing 'lang' key in JSON response.")
            
            self.finished.emit(parsed_json)
        except Exception as e:
            self.error.emit(f"Error during translation: {e}")

class PreviewDialog(QDialog):
    def __init__(self, main_app, keys, langs, api_params, batch_size):
        super().__init__(main_app)
        self.main_app = main_app
        self.all_keys = list(keys)
        self.keys_to_process = list(keys)
        self.langs = langs
        self.api_params = api_params
        self.batch_size = batch_size
        self.translation_cache = self.main_app.translation_cache  # Store translations per item ID
        self.worker = None
        self._init_ui()

    def _cleanup_worker(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        self.worker = None

    def reject(self):
        self._cleanup_worker()
        super().reject()

    def accept(self):
        self._cleanup_worker()
        super().accept()

    def closeEvent(self, event):
        self._cleanup_worker()
        super().closeEvent(event)

    def _init_ui(self):
        self.setWindowTitle("Preview and Test Translations")
        self.setMinimumSize(1000, 600)
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Panel (Keys)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        keys_header_layout = QHBoxLayout()
        keys_header_layout.addWidget(QLabel("English Keys & Text:"))
        self.preview_select_all_btn = QPushButton("Un/Select All")
        self.preview_select_all_btn.clicked.connect(self._toggle_select_all)
        keys_header_layout.addWidget(self.preview_select_all_btn)
        left_layout.addLayout(keys_header_layout)

        self.keys_list = QListWidget()
        for k in self.all_keys:
            item = QListWidgetItem(f"[{k['uid']}] {k['key']}\n  - {k['text']}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, k)
            self.keys_list.addItem(item)
        self.keys_list.currentItemChanged.connect(self._on_key_selected)
        self._update_list_colors()
        left_layout.addWidget(self.keys_list)
        splitter.addWidget(left_widget)

        # Right Panel (Results)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Translation Test Results:"))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        right_layout.addWidget(self.result_text)
        splitter.addWidget(right_widget)

        layout.addWidget(splitter, 1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.test_one_btn = QPushButton("Test Highlighted")
        self.test_one_btn.clicked.connect(self.test_one)
        btn_layout.addWidget(self.test_one_btn)

        self.save_key_btn = QPushButton("Save Key")
        self.save_key_btn.clicked.connect(self.save_key)
        self.save_key_btn.setEnabled(False)
        btn_layout.addWidget(self.save_key_btn)

        self.translate_selected_btn = QPushButton("Translate Selected")
        self.translate_selected_btn.clicked.connect(lambda: self.run_translation(mode='selected'))
        btn_layout.addWidget(self.translate_selected_btn)

        btn_layout.addStretch()

        self.translate_all_btn = QPushButton("Translate All")
        self.translate_all_btn.setStyleSheet("background-color: #23d18b; color: white;")
        self.translate_all_btn.clicked.connect(lambda: self.run_translation(mode='all'))
        btn_layout.addWidget(self.translate_all_btn)

        self.save_translated_btn = QPushButton("Save Translated")
        self.save_translated_btn.setStyleSheet("background-color: #29b8db; color: white;")
        self.save_translated_btn.clicked.connect(self._finalize_translations)
        self.save_translated_btn.setEnabled(False)
        btn_layout.addWidget(self.save_translated_btn)

        layout.addLayout(btn_layout)

    def _toggle_select_all(self):

        if self.keys_list.count() == 0: return
        new_state = Qt.CheckState.Unchecked if self.keys_list.item(0).checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
        for i in range(self.keys_list.count()):
            self.keys_list.item(i).setCheckState(new_state)
    
    def _update_list_colors(self):
        for i in range(self.keys_list.count()):
            item = self.keys_list.item(i)
            orig_item = item.data(Qt.ItemDataRole.UserRole)
            item_id = f"{orig_item['uid']}:{orig_item['section']}:{orig_item['key']}"
            if item_id in self.translation_cache:
                item.setForeground(QColor("#23d18b"))
            else:
                item.setForeground(QColor("#d4d4d4"))

    def _on_key_selected(self, current, previous):
        if not current:
            self.result_text.clear()
            self.save_key_btn.setEnabled(False)
            return

        orig_item = current.data(Qt.ItemDataRole.UserRole)
        item_id = f"{orig_item['uid']}:{orig_item['section']}:{orig_item['key']}"

        if item_id in self.translation_cache:
            self.result_text.setPlainText(json.dumps(self.translation_cache[item_id], indent=2, ensure_ascii=False))
            self.save_key_btn.setEnabled(True)
        else:
            self.result_text.clear()
            self.save_key_btn.setEnabled(False)

    def test_one(self):
        current_item = self.keys_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please highlight a key in the list to test.")
            return

        orig_item = current_item.data(Qt.ItemDataRole.UserRole)
        self.main_app.log("Testing one key...")
        self.result_text.clear()
        self.save_key_btn.setEnabled(False)
        self._cleanup_worker()
        self.worker = TranslatorWorker(keys=[orig_item], target_langs=self.langs, **self.api_params)
        self.worker.finished.connect(lambda result: self._on_test_finished(result, orig_item))
        self.worker.error.connect(self.main_app._on_worker_error)
        self.worker.start()

    def _on_test_finished(self, result_json, orig_item):
        item_id = f"{orig_item['uid']}:{orig_item['section']}:{orig_item['key']}"
        self.translation_cache[item_id] = result_json
        self._update_list_colors()

        # Refresh UI if it's still selected
        current_item = self.keys_list.currentItem()
        if current_item and current_item.data(Qt.ItemDataRole.UserRole) == orig_item:
            self.result_text.setPlainText(json.dumps(result_json, indent=2, ensure_ascii=False))
            self.save_key_btn.setEnabled(True)

        self.main_app.log("Test finished. Result cached and displayed in preview.")

    def save_key(self):
        current_item = self.keys_list.currentItem()
        if not current_item: return

        orig_item = current_item.data(Qt.ItemDataRole.UserRole)
        item_id = f"{orig_item['uid']}:{orig_item['section']}:{orig_item['key']}"

        if item_id not in self.translation_cache:
            QMessageBox.warning(self, "Warning", "No translation available for this key.")
            return

        try:
            parsed_json = self.translation_cache[item_id]
            if "lang" not in parsed_json: return

            translations_to_apply =[]
            for lang_code, translations in parsed_json["lang"].items():
                if lang_code not in self.langs: continue
                key_name = orig_item['key']
                if key_name in translations:
                    base_dir = os.path.dirname(orig_item['path'])
                    target_file = os.path.join(base_dir, f"{lang_code}.tslang")
                    translations_to_apply.append({
                        'file_path': target_file, 'uid': orig_item['uid'], 'lang': lang_code,
                        'section': orig_item['section'], 'key': key_name, 'text': translations[key_name]
                    })

            safe, conflicts = self.main_app._check_translations(translations_to_apply)
            self.main_app._on_worker_finished(safe, conflicts)
            self.save_key_btn.setEnabled(False)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save key: {e}")

    def run_translation(self, mode='all'):
        if mode == 'all':
            self.keys_to_process =[self.keys_list.item(i).data(Qt.ItemDataRole.UserRole) 
                                    for i in range(self.keys_list.count()) 
                                    if self.keys_list.item(i).checkState() == Qt.CheckState.Checked]
        elif mode == 'selected':
            selected_items =[self.keys_list.item(i).data(Qt.ItemDataRole.UserRole)
                              for i in range(self.keys_list.count())
                              if self.keys_list.item(i).checkState() == Qt.CheckState.Checked]
            self.keys_to_process = selected_items

        if not self.keys_to_process:
            QMessageBox.warning(self, "Warning", "No keys are checked for translation.")
            return

        self.set_buttons_enabled(False)
        self.save_translated_btn.setEnabled(False)
        self.all_translations_to_apply =[]
        self._process_next_batch()

    def _process_next_batch(self):
        if not self.keys_to_process:
            self.main_app.log("All batches processed. Please review and click 'Save Translated'.")
            self.set_buttons_enabled(True)
            self.save_translated_btn.setEnabled(True)
            return

        batch = self.keys_to_process[:self.batch_size]
        self.keys_to_process = self.keys_to_process[self.batch_size:]

        self.main_app.log(f"Processing batch of {len(batch)} keys...")
        self._cleanup_worker()
        self.worker = TranslatorWorker(keys=batch, target_langs=self.langs, **self.api_params)
        self.worker.finished.connect(lambda result: self._on_batch_finished(result, batch))
        self.worker.error.connect(self._on_batch_error)
        self.worker.start()

    def _on_batch_finished(self, result_json, original_batch):
        for orig_item in original_batch:
            item_id = f"{orig_item['uid']}:{orig_item['section']}:{orig_item['key']}"
            key_name = orig_item['key']

            item_json = {"lang": {}}
            has_trans = False

            for lang_code, translations in result_json.get("lang", {}).items():
                if key_name in translations:
                    item_json["lang"][lang_code] = {key_name: translations[key_name]}
                    has_trans = True

                    base_dir = os.path.dirname(orig_item['path'])
                    target_file = os.path.join(base_dir, f"{lang_code}.tslang")
                    self.all_translations_to_apply.append({
                        'file_path': target_file, 'uid': orig_item['uid'], 'lang': lang_code,
                        'section': orig_item['section'], 'key': key_name, 'text': translations[key_name]
                    })

            if has_trans:
                self.translation_cache[item_id] = item_json
        self._update_list_colors()

        # Refresh UI for currently selected item just in case it was in this batch
        current_item = self.keys_list.currentItem()
        if current_item:
            self._on_key_selected(current_item, None)

        self._process_next_batch()

    def _on_batch_error(self, error_msg):
        self.main_app._on_worker_error(error_msg)
        self.set_buttons_enabled(True)

    def _finalize_translations(self):
        self.main_app.log("Checking for conflicts...")
        safe, conflicts = self.main_app._check_translations(self.all_translations_to_apply)
        self.main_app._on_worker_finished(safe, conflicts)
        self.save_translated_btn.setEnabled(False)
        self.accept()

    def set_buttons_enabled(self, enabled):
        self.test_one_btn.setEnabled(enabled)
        self.translate_selected_btn.setEnabled(enabled)
        self.translate_all_btn.setEnabled(enabled)
        self.preview_select_all_btn.setEnabled(enabled)


class AutoTranslatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ELAI-DevKit Auto Translator")
        self.resize(1000, 700)
        
        self.root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.en_data =[]
        self.translation_cache = {}

        self._init_ui()
        self._scan_project()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout(api_group)
        self.url_input = QLineEdit("https://api.openai.com/v1/chat/completions")
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.model_input = QLineEdit("gpt-4o-mini")
        
        api_layout.addRow("Endpoint URL:", self.url_input)
        api_layout.addRow("API Key:", self.key_input)
        api_layout.addRow("Model:", self.model_input)
        
        api_actions_layout = QHBoxLayout()
        self.test_api_btn = QPushButton("Test API & Model")
        self.test_api_btn.clicked.connect(self._test_api)
        api_actions_layout.addWidget(self.test_api_btn)
        api_actions_layout.addStretch()
        api_layout.addRow("", api_actions_layout)
        
        main_layout.addWidget(api_group)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        target_widget = QWidget()
        target_layout = QVBoxLayout(target_widget)
        
        target_header_layout = QHBoxLayout()
        target_header_layout.addWidget(QLabel("1. Select Targets:"))
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._scan_project)
        target_header_layout.addWidget(self.refresh_btn)
        target_layout.addLayout(target_header_layout)
        
        self.target_list = QListWidget()
        self.target_list.itemChanged.connect(self._on_target_changed)
        target_layout.addWidget(self.target_list)
        splitter.addWidget(target_widget)

        keys_widget = QWidget()
        keys_layout = QVBoxLayout(keys_widget)
        
        keys_header_layout = QHBoxLayout()
        keys_header_layout.addWidget(QLabel("2. Select Keys to Translate:"))
        self.select_all_keys_btn = QPushButton("Un/Select All")
        self.select_all_keys_btn.clicked.connect(self._select_all_keys)
        keys_header_layout.addWidget(self.select_all_keys_btn)
        keys_layout.addLayout(keys_header_layout)
        
        self.keys_list = QListWidget()
        keys_layout.addWidget(self.keys_list)
        splitter.addWidget(keys_widget)

        lang_widget = QWidget()
        lang_layout = QVBoxLayout(lang_widget)
        lang_layout.addWidget(QLabel("3. Target Languages:"))
        
        self.lang_list = QListWidget()
        lang_layout.addWidget(self.lang_list)

        add_lang_layout = QHBoxLayout()
        self.new_lang_input = QLineEdit()
        self.new_lang_input.setPlaceholderText("Language code...")
        add_lang_btn = QPushButton("Add")
        add_lang_btn.clicked.connect(self._add_language)
        add_lang_layout.addWidget(self.new_lang_input)
        add_lang_layout.addWidget(add_lang_btn)
        lang_layout.addLayout(add_lang_layout)

        lang_layout.addWidget(QLabel("Batch Size (keys per request):"))
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 20)
        self.batch_spin.setValue(2)
        lang_layout.addWidget(self.batch_spin)
        
        splitter.addWidget(lang_widget)
        main_layout.addWidget(splitter, stretch=2)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output, stretch=1)

        self.translate_btn = QPushButton("Preview & Translate")
        self.translate_btn.setStyleSheet("background-color: #23d18b; color: white; font-weight: bold; padding: 10px;")
        self.translate_btn.clicked.connect(self._start_translation)
        main_layout.addWidget(self.translate_btn)

    def _test_api(self):
        url = self.url_input.text().strip()
        key = self.key_input.text().strip()
        model = self.model_input.text().strip()
        
        if not url or not model:
            QMessageBox.warning(self, "Warning", "API URL and Model are required to test.")
            return
            
        self.log("Testing API Connection...")
        self.test_api_btn.setEnabled(False)
        QApplication.processEvents()
        
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
            
        payload = {
            "model": model,
            "messages":[{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
            "stream": False
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if not resp.ok:
                self.log(f"API Test Failed with status {resp.status_code}: {resp.text}")
                QMessageBox.critical(self, "Error", f"API Connection Failed:\nStatus: {resp.status_code}\nResponse: {resp.text}")
                return

            try:
                if resp.text.strip().startswith("data:"):
                    resp_data = {"choices": [{}]}
                else:
                    resp_data = resp.json()
            except Exception as e:
                self.log(f"API Test Failed: Invalid JSON response. Raw text: {resp.text}")
                QMessageBox.critical(self, "Error", f"API Connection Failed:\nInvalid JSON. Raw text:\n{resp.text}")
                return

            if "choices" in resp_data:
                self.log("API Test Successful! Model is accessible.")
                QMessageBox.information(self, "Success", "API Connection Successful! Model is accessible.")
            else:
                self.log(f"API Test Warning: Unexpected response format: {resp_data}")
                QMessageBox.warning(self, "Warning", "Connection succeeded, but response format is unexpected.")
        except Exception as e:
            self.log(f"API Test Failed: {e}")
            QMessageBox.critical(self, "Error", f"API Connection Failed:\n{e}")
        finally:
            self.test_api_btn.setEnabled(True)

    def _scan_project(self):
        self.en_data =[]
        self.target_list.clear()
        self.keys_list.clear()
        self.lang_list.clear()

        scan_paths =[
            os.path.join(self.root_path, 'assets', 'translation'),
            os.path.join(self.root_path, 'apps')
        ]
        
        found_langs = set()
        
        for path in scan_paths:
            if not os.path.exists(path): continue
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith('.tslang'):
                        lang_code = file[:-7]
                        if lang_code == 'en':
                            file_path = os.path.join(root, file)
                            self._parse_en_tslang(file_path)
                        else:
                            found_langs.add(lang_code)
                    
        for data in self.en_data:
            item = QListWidgetItem(f"{data['uid']} ({data['path']})")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, data)
            self.target_list.addItem(item)
            
        for lang_code in sorted(list(found_langs)):
            item = QListWidgetItem(lang_code)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.lang_list.addItem(item)
            
        self.log(f"Scanned project. Found {len(self.en_data)} targets and {len(found_langs)} translation languages.")

    def _parse_en_tslang(self, path):
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            uid = root.get('uid', 'unknown')
            
            keys =[]
            for section in root.findall('section'):
                sec_name = section.get('name', 'Default')
                for key_node in section.findall('key'):
                    key_name = key_node.get('name')
                    text = key_node.text or ""
                    if key_name and text:
                        keys.append({
                            'uid': uid, 'path': path, 'section': sec_name,
                            'key': key_name, 'text': text
                        })
                        
            self.en_data.append({'uid': uid, 'path': path, 'keys': keys})
        except Exception as e:
            self.log(f"Failed to parse {path}: {e}")

    def _on_target_changed(self):
        self.keys_list.clear()
        for i in range(self.target_list.count()):
            item = self.target_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                for k in data['keys']:
                    k_item = QListWidgetItem(f"[{data['uid']}] {k['key']}")
                    k_item.setFlags(k_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    k_item.setCheckState(Qt.CheckState.Checked)
                    k_item.setData(Qt.ItemDataRole.UserRole, k)
                    self.keys_list.addItem(k_item)

    def _select_all_keys(self):
        if self.keys_list.count() == 0: return
        first_item = self.keys_list.item(0)
        new_state = Qt.CheckState.Unchecked if first_item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
        for i in range(self.keys_list.count()):
            self.keys_list.item(i).setCheckState(new_state)

    def _add_language(self):
        new_lang = self.new_lang_input.text().strip().lower()
        if new_lang:
            for i in range(self.lang_list.count()):
                if self.lang_list.item(i).text() == new_lang: return
            
            item = QListWidgetItem(new_lang)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.lang_list.addItem(item)
            self.new_lang_input.clear()

    def log(self, message):
        self.log_output.append(message)

    def _start_translation(self):
        selected_keys =[]
        for i in range(self.keys_list.count()):
            item = self.keys_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_keys.append(item.data(Qt.ItemDataRole.UserRole))

        if not selected_keys:
            QMessageBox.warning(self, "Warning", "No keys selected for translation.")
            return

        target_langs =[]
        for i in range(self.lang_list.count()):
            item = self.lang_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                target_langs.append(item.text())

        if not target_langs:
            QMessageBox.warning(self, "Warning", "No target languages selected.")
            return

        api_params = {
            "api_url": self.url_input.text().strip(),
            "api_key": self.key_input.text().strip(),
            "model": self.model_input.text().strip()
        }
        
        if not api_params["api_url"] or not api_params["model"]:
            QMessageBox.warning(self, "Warning", "API URL and Model are required.")
            return

        preview_dialog = PreviewDialog(self, selected_keys, target_langs, api_params, self.batch_spin.value())
        preview_dialog.exec()

    def _on_worker_error(self, err_msg):
        self.log(f"ERROR: {err_msg}")
        self.translate_btn.setEnabled(True)

    def _check_translations(self, translations):
        safe_to_apply, conflicts = [],[]
        for task in translations:
            has_conflict = False
            if os.path.exists(task['file_path']):
                try:
                    tree = ET.parse(task['file_path'])
                    root = tree.getroot()
                    sec_node = root.find(f".//section[@name='{task['section']}']")
                    if sec_node is not None:
                        key_node = sec_node.find(f".//key[@name='{task['key']}']")
                        if key_node is not None and key_node.text and key_node.text.strip():
                            task['existing_text'] = key_node.text
                            conflicts.append(task)
                            has_conflict = True
                except Exception: pass
            if not has_conflict: safe_to_apply.append(task)
        return safe_to_apply, conflicts

    def _on_worker_finished(self, safe_to_apply, conflicts):
        final_tasks = list(safe_to_apply)
        if conflicts:
            dialog = ConflictDialog(conflicts, self)
            if dialog.exec():
                overwrites = dialog.get_overwrites()
                final_tasks.extend(overwrites)
                self.log(f"User approved {len(overwrites)} overwrites out of {len(conflicts)} conflicts.")
            else:
                self.log("Conflicts dialog cancelled. Skipping conflicting keys.")
        if final_tasks:
            self._write_translations(final_tasks)
        else:
            self.log("No translations to apply.")
        self.log("Process complete.")
        self.translate_btn.setEnabled(True)

    def _write_translations(self, tasks):
        self.log("Writing updates to file system...")
        file_groups = defaultdict(list)
        for task in tasks: file_groups[task['file_path']].append(task)

        for file_path, file_tasks in file_groups.items():
            try:
                if os.path.exists(file_path):
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                else:
                    first_task = file_tasks[0]
                    root = ET.Element("tslang", uid=first_task['uid'], lang=first_task['lang'])
                    tree = ET.ElementTree(root)

                for task in file_tasks:
                    sec_node = root.find(f"./section[@name='{task['section']}']")
                    if sec_node is None: sec_node = ET.SubElement(root, "section", name=task['section'])
                    key_node = sec_node.find(f"./key[@name='{task['key']}']")
                    if key_node is None: key_node = ET.SubElement(sec_node, "key", name=task['key'])
                    key_node.text = task['text']

                if hasattr(ET, "indent"): ET.indent(tree, space="    ")
                tree.write(file_path, encoding="utf-8", xml_declaration=True)
                self.log(f"Updated {os.path.basename(file_path)} ({len(file_tasks)} keys)")
            except Exception as e:
                self.log(f"Failed to write {file_path}: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoTranslatorApp()
    window.show()
    sys.exit(app.exec())