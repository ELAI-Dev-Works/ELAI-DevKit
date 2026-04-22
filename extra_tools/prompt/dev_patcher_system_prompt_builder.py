import sys
import os
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QTextEdit, QPushButton, QFileDialog, QMessageBox,
    QGroupBox
)
from PySide6.QtCore import Qt

class PromptBuilderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DevPatcher System Prompt Builder")
        self.setGeometry(100, 100, 960, 640)

        # Define paths relative to the script location
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.templates_path = os.path.join(self.base_path, 'templates')
        # Go up two levels from extra_tools/prompt to the project root
        self.project_root = os.path.dirname(os.path.dirname(self.base_path))
        self.docs_path = os.path.join(self.project_root, 'apps', 'dev_patcher', 'doc', 'categories', 'commands_and_syntax', 'syntax.md')

        self.init_ui()
        self.load_all_templates()
        self.load_documentation()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # --- Sections for each part of the prompt ---
        self.start_group = self.create_section_group("START", "start")
        self.instruction_group = self.create_section_group("INSTRUCTION", "instruction")
        self.rules_group = self.create_section_group("RULES", "rules")
        self.documentation_group = self.create_documentation_group("DOCUMENTATION")

        # Layout for the top sections
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.start_group)
        top_layout.addWidget(self.instruction_group)
        top_layout.addWidget(self.rules_group)
        main_layout.addLayout(top_layout)

        main_layout.addWidget(self.documentation_group)

        # --- Assemble and Save section ---
        assemble_layout = QHBoxLayout()
        self.assemble_btn = QPushButton("Assemble Prompt")
        self.assemble_btn.clicked.connect(self.assemble_prompt)
        assemble_layout.addWidget(self.assemble_btn)
        assemble_layout.addStretch()
        self.save_assembled_btn = QPushButton("Save Assembled Prompt...")
        self.save_assembled_btn.clicked.connect(self.save_assembled_prompt)
        assemble_layout.addWidget(self.save_assembled_btn)
        main_layout.addLayout(assemble_layout)

        # --- Final Prompt Display ---
        self.final_prompt_edit = QTextEdit()
        self.final_prompt_edit.setPlaceholderText("Assembled prompt will appear here...")
        main_layout.addWidget(self.final_prompt_edit)

    def create_section_group(self, title, prefix):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        combo = QComboBox()
        combo.setPlaceholderText("Select a variant...")
        setattr(self, f"{prefix}_combo", combo)

        text_edit = QTextEdit()
        setattr(self, f"{prefix}_edit", text_edit)

        save_btn = QPushButton("Save as New Variant")
        save_btn.clicked.connect(lambda: self.save_variant(prefix))

        layout.addWidget(combo)
        layout.addWidget(text_edit, 1) # Give it stretch
        layout.addWidget(save_btn)

        combo.currentIndexChanged.connect(lambda: self.load_template(prefix))
        return group

    def create_documentation_group(self, title):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        self.docs_edit = QTextEdit()
        self.docs_edit.setReadOnly(True)
        layout.addWidget(self.docs_edit)
        return group

    def load_all_templates(self):
        for prefix in ["start", "instruction", "rules"]:
            self.load_templates_for_prefix(prefix)

    def load_templates_for_prefix(self, prefix):
        combo = getattr(self, f"{prefix}_combo")
        combo.blockSignals(True)
        combo.clear()
        variants = self._find_templates(prefix)
        for num, path in sorted(variants.items()):
            combo.addItem(f"Variant [{num}]", path)
        combo.blockSignals(False)
        if combo.count() > 0:
            combo.setCurrentIndex(0)
            self.load_template(prefix)

    def _find_templates(self, prefix):
        variants = {}
        if not os.path.exists(self.templates_path):
            return variants
        pattern = re.compile(rf"{prefix}_\(variant_\[(\d+)\]\)\.txt")
        for filename in os.listdir(self.templates_path):
            match = pattern.match(filename)
            if match:
                variant_num = int(match.group(1))
                variants[variant_num] = os.path.join(self.templates_path, filename)
        return variants

    def load_template(self, prefix):
        combo = getattr(self, f"{prefix}_combo")
        text_edit = getattr(self, f"{prefix}_edit")
        path = combo.currentData()
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    text_edit.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load file {path}:\n{e}")
        else:
            text_edit.clear()

    def load_documentation(self):
        if os.path.exists(self.docs_path):
            try:
                with open(self.docs_path, 'r', encoding='utf-8') as f:
                    self.docs_edit.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load documentation file {self.docs_path}:\n{e}")
                self.docs_edit.setPlainText(f"Error loading file: {e}")
        else:
            self.docs_edit.setPlainText(f"Documentation file not found at:\n{self.docs_path}")

    def save_variant(self, prefix):
        text_edit = getattr(self, f"{prefix}_edit")
        content = text_edit.toPlainText()
        if not content:
            QMessageBox.warning(self, "Warning", "Cannot save empty content as a new variant.")
            return

        variants = self._find_templates(prefix)
        next_variant_num = max(variants.keys()) + 1 if variants else 1
        new_filename = f"{prefix}_(variant_[{next_variant_num}]).txt"
        new_filepath = os.path.join(self.templates_path, new_filename)

        try:
            os.makedirs(self.templates_path, exist_ok=True)
            with open(new_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Success", f"Saved new variant as {new_filename}")
            self.load_templates_for_prefix(prefix)
            # Set the combo box to the newly created item
            combo = getattr(self, f"{prefix}_combo")
            index = combo.findData(new_filepath)
            if index != -1:
                combo.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save new variant:\n{e}")

    def assemble_prompt(self):
        start_text = self.start_edit.toPlainText()
        instruction_text = self.instruction_edit.toPlainText()
        docs_text = self.docs_edit.toPlainText()
        rules_text = self.rules_edit.toPlainText()

        assembled_text = (
            f"[<START>]\n"
            f"{start_text}\n"
            f"[<INSTRUCTION>]\n"
            f"{instruction_text}\n"
            f"[<DOCUMENTATION>]\n"
            f"{docs_text}\n"
            f"[<RULES>]\n"
            f"{rules_text}\n"
            f"[<END>]"
        )
        self.final_prompt_edit.setPlainText(assembled_text)
        QMessageBox.information(self, "Success", "Prompt assembled!")

    def save_assembled_prompt(self):
        content = self.final_prompt_edit.toPlainText()
        if not content:
            QMessageBox.warning(self, "Warning", "There is no assembled prompt to save.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Assembled Prompt", self.base_path, "Text Files (*.txt)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "Success", f"Prompt saved to {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PromptBuilderWindow()
    window.show()
    sys.exit(app.exec())