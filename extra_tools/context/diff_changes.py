#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ELAI-DevKit Extra Tool: Project Pack Diff & Change Generator

Compares two `_project_pack.txt` files (old and new) and generates a
`Project_changes.txt` file with only the differences from the new version.
Files that were deleted from the project are also listed.

Usage: Run this script from the extra_tools menu or directly.
"""

import sys
import os
import difflib
import re
from typing import Dict, List, Tuple, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal


# ----------------------------------------------------------------------
# Parsing logic for _project_pack.txt files
# ----------------------------------------------------------------------

def parse_pack_file(file_path: str, progress_callback=None) -> Dict[str, List[str]]:
    """
    Parse a project pack file into a dictionary:
        key: relative file path (e.g., 'src/main.py')
        value: list of content lines (without line numbers and without the
               leading '#//> ' marker and trailing separator).
    """
    result = {}
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    total_lines = len(lines)
    i = 0
    while i < total_lines:
        line = lines[i].rstrip('\n')
        # Detect start of a file block: "#//> project_name/relative_path:"
        if line.startswith('#//> '):
            # Extract the path after the first slash
            marker = line[5:]  # remove '#//> '
            if ':' in marker:
                file_path_part = marker[:marker.rfind(':')]
                # The marker format is "ProjectName/relative/path/file.py:"
                # Find the first slash to separate project name from relative path
                slash_idx = file_path_part.find('/')
                if slash_idx != -1:
                    rel_path = file_path_part[slash_idx+1:]
                else:
                    rel_path = file_path_part
            else:
                rel_path = ""

            # Read content until the separator "================================================================================"
            content_lines = []
            i += 1
            while i < total_lines and not lines[i].startswith('================================================================================'):
                content_line = lines[i].rstrip('\n')
                # Strip line numbers: remove leading spaces, digits, and the '|'
                # Format example: " 1| from PySide6..."
                stripped = re.sub(r'^\s*\d+\|', '', content_line)
                stripped = stripped.rstrip('\n')
                content_lines.append(stripped)
                i += 1
            # Skip the separator line (if any)
            if i < total_lines and lines[i].startswith('================================================================================'):
                i += 1
            # Store only non-empty paths (ignore empty markers)
            if rel_path and content_lines:
                result[rel_path] = content_lines
            if progress_callback:
                progress_callback(int(100 * i / total_lines))
        else:
            i += 1

    return result


# ----------------------------------------------------------------------
# Diff generation
# ----------------------------------------------------------------------

def generate_changes_report(
    old_data: Dict[str, List[str]],
    new_data: Dict[str, List[str]],
    new_file_path: str
) -> str:
    """
    Generate a human-readable report of changes from old to new.
    Returns a string that will be saved as Project_changes.txt.
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("PROJECT CHANGES REPORT")
    report_lines.append(f"Generated from: {os.path.basename(new_file_path)}")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Determine added, removed, common
    old_paths = set(old_data.keys())
    new_paths = set(new_data.keys())
    added = new_paths - old_paths
    removed = old_paths - new_paths
    common = old_paths & new_paths

    # Summary
    report_lines.append(f"Summary:")
    report_lines.append(f"  Files added   : {len(added)}")
    report_lines.append(f"  Files removed : {len(removed)}")
    report_lines.append(f"  Files modified: ? (calculated below)")
    report_lines.append("")

    # Added files
    if added:
        report_lines.append("-" * 80)
        report_lines.append("ADDED FILES:")
        report_lines.append("-" * 80)
        for path in sorted(added):
            report_lines.append(f"\n[+] {path}")
            report_lines.append("--- New file content ---")
            for line in new_data[path]:
                report_lines.append(line)
            report_lines.append("--- End of new file ---")
        report_lines.append("")

    # Removed files
    if removed:
        report_lines.append("-" * 80)
        report_lines.append("REMOVED FILES:")
        report_lines.append("-" * 80)
        for path in sorted(removed):
            report_lines.append(f"\n[-] {path}")
            report_lines.append("This file is present in the old version but missing in the new version.")
        report_lines.append("")

    # Modified files (content differs)
    modified_count = 0
    for path in sorted(common):
        old_lines = old_data[path]
        new_lines = new_data[path]
        if old_lines != new_lines:
            modified_count += 1
            report_lines.append("-" * 80)
            report_lines.append(f"MODIFIED FILE: {path}")
            report_lines.append("-" * 80)
            # Generate unified diff between old and new (without line numbers from pack)
            diff = difflib.unified_diff(
                old_lines, new_lines,
                fromfile=f'old/{path}', tofile=f'new/{path}',
                lineterm=''
            )
            diff_lines = list(diff)
            if diff_lines:
                report_lines.extend(diff_lines)
            else:
                report_lines.append("(Content differs but diff could not be generated)")
            report_lines.append("")

    # Update summary with modified count
    new_summary = []
    for line in report_lines:
        if line.startswith("  Files modified:"):
            new_summary.append(f"  Files modified: {modified_count}")
        else:
            new_summary.append(line)
    report_lines = new_summary

    # Footer
    report_lines.append("=" * 80)
    report_lines.append("End of changes report.")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)


# ----------------------------------------------------------------------
# Worker thread for background processing
# ----------------------------------------------------------------------

class DiffWorker(QThread):
    progress = Signal(int)
    finished = Signal(str, str)   # report_content, error_message (error_message is empty on success)
    error = Signal(str)

    def __init__(self, old_path: str, new_path: str):
        super().__init__()
        self.old_path = old_path
        self.new_path = new_path

    def run(self):
        try:
            # Parse old file
            self.progress.emit(10)
            old_data = parse_pack_file(self.old_path, lambda v: self.progress.emit(int(10 + v * 0.4)))
            self.progress.emit(50)

            # Parse new file
            new_data = parse_pack_file(self.new_path, lambda v: self.progress.emit(int(50 + v * 0.4)))
            self.progress.emit(90)

            # Generate report
            report = generate_changes_report(old_data, new_data, self.new_path)
            self.progress.emit(100)
            self.finished.emit(report, "")
        except Exception as e:
            self.error.emit(str(e))


# ----------------------------------------------------------------------
# Main GUI Window
# ----------------------------------------------------------------------

class DiffChangesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Pack Diff & Change Generator")
        self.setMinimumSize(900, 700)

        # Variables
        self.old_file_path = ""
        self.new_file_path = ""
        self.worker = None

        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # File selection group
        file_group = QVBoxLayout()
        file_group.setSpacing(10)

        # Old file
        old_layout = QHBoxLayout()
        old_layout.addWidget(QLabel("Old project pack (base):"))
        self.old_edit = QLineEdit()
        self.old_edit.setReadOnly(True)
        self.old_btn = QPushButton("Browse...")
        self.old_btn.clicked.connect(lambda: self._browse_file(is_old=True))
        old_layout.addWidget(self.old_edit, 1)
        old_layout.addWidget(self.old_btn)
        file_group.addLayout(old_layout)

        # New file
        new_layout = QHBoxLayout()
        new_layout.addWidget(QLabel("New project pack (latest):"))
        self.new_edit = QLineEdit()
        self.new_edit.setReadOnly(True)
        self.new_btn = QPushButton("Browse...")
        self.new_btn.clicked.connect(lambda: self._browse_file(is_old=False))
        new_layout.addWidget(self.new_edit, 1)
        new_layout.addWidget(self.new_btn)
        file_group.addLayout(new_layout)

        layout.addLayout(file_group)

        # Action buttons
        action_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate Changes")
        self.generate_btn.clicked.connect(self._generate)
        self.save_btn = QPushButton("Save Changes Report...")
        self.save_btn.clicked.connect(self._save_report)
        self.save_btn.setEnabled(False)
        action_layout.addStretch()
        action_layout.addWidget(self.generate_btn)
        action_layout.addWidget(self.save_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Progress bar (simple label, can be upgraded to QProgressBar)
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFontFamily("Courier New")
        layout.addWidget(self.output_text, 1)

    def _apply_styles(self):
        # Simple style to match ELAI-DevKit aesthetics (dark friendly)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel, QPushButton, QLineEdit {
                color: #f0f0f0;
                background-color: #2d2d2d;
                border: none;
            }
            QLineEdit {
                padding: 4px;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
                background-color: #0e639c;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0a4f7a;
            }
            QTextEdit {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                font-family: monospace;
            }
        """)

    def _browse_file(self, is_old: bool):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select project pack file", "",
            "Project pack files (*_project_pack.txt);;All files (*)"
        )
        if not file_path:
            return
        if is_old:
            self.old_file_path = file_path
            self.old_edit.setText(file_path)
        else:
            self.new_file_path = file_path
            self.new_edit.setText(file_path)
        # Reset output when a file changes
        self.output_text.clear()
        self.save_btn.setEnabled(False)
        self.progress_label.setText("")

    def _generate(self):
        if not self.old_file_path or not self.new_file_path:
            QMessageBox.warning(self, "Missing files", "Please select both old and new project pack files.")
            return
        # Disable buttons during processing
        self.generate_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.output_text.clear()
        self.progress_label.setText("Processing...")

        # Start worker thread
        self.worker = DiffWorker(self.old_file_path, self.new_file_path)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _update_progress(self, value: int):
        self.progress_label.setText(f"Processing... {value}%")
        if value >= 100:
            self.progress_label.setText("Done!")

    def _on_finished(self, report: str, error_msg: str):
        self.generate_btn.setEnabled(True)
        if error_msg:
            QMessageBox.critical(self, "Error", f"Failed to generate diff:\n{error_msg}")
            return
        self.output_text.setPlainText(report)
        self.save_btn.setEnabled(True)
        self.progress_label.setText("Ready - changes ready to save.")

    def _on_error(self, err_msg: str):
        self.generate_btn.setEnabled(True)
        self.progress_label.setText("Error occurred.")
        QMessageBox.critical(self, "Processing Error", str(err_msg))

    def _save_report(self):
        report = self.output_text.toPlainText()
        if not report.strip():
            QMessageBox.warning(self, "No changes", "No changes report to save.")
            return

        # Suggest default output location (next to the new pack file)
        if self.new_file_path:
            default_dir = os.path.dirname(self.new_file_path)
            default_name = "Project_changes.txt"
        else:
            default_dir = os.getcwd()
            default_name = "Project_changes.txt"

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save changes report", os.path.join(default_dir, default_name),
            "Text files (*.txt);;All files (*)"
        )
        if not save_path:
            return
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report)
            QMessageBox.information(self, "Saved", f"Changes report saved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{e}")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    window = DiffChangesWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()