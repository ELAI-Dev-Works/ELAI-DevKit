import difflib
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QScrollArea, QWidget, QFrame, QDialogButtonBox, QMessageBox,
    QLineEdit
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt

class CorrectorDialog(QDialog):
    def __init__(self, issues, original_patch, main_window, qs_widget):
        super().__init__(main_window)
        self.main_window = main_window
        self.qs_widget = qs_widget
        self.lang = main_window.lang
        self.issues = issues
        self.original_patch = original_patch
        self.corrected_patch = original_patch
        self.issue_widgets = []
        self.patch_was_modified = False

        self.setWindowTitle(self.lang.get('corrector_title'))
        self.setMinimumSize(800, 600)

        self._init_ui()
        self._populate_issues()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        info_label = QLabel(self.lang.get('corrector_info_label'))
        main_layout.addWidget(info_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.issues_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.button_box = QDialogButtonBox()
        self.apply_all_btn = self.button_box.addButton(self.lang.get('corrector_apply_all_btn'), QDialogButtonBox.ButtonRole.ActionRole)
        self.apply_all_btn.clicked.connect(self._apply_all_fixes)

        self.accept_btn = self.button_box.addButton(self.lang.get('corrector_accept_btn'), QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_btn = self.button_box.addButton(self.lang.get('corrector_cancel_btn'), QDialogButtonBox.ButtonRole.RejectRole)
        self.accept_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        main_layout.addWidget(self.button_box)

    def _populate_issues(self):
        for i, issue in enumerate(self.issues):
            issue_widget = self._create_issue_widget(issue, i)
            self.issues_layout.addWidget(issue_widget)
            self.issue_widgets.append(issue_widget)
        self.issues_layout.addStretch()

    def _create_issue_widget(self, issue, index):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)

        desc_label = QLabel(f"<b>{self.lang.get('corrector_issue_label')} #{index+1}:</b> {issue['description']}")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        text_view = QTextEdit()
        text_view.setReadOnly(True)
        text_view.setFont(QFont("Courier New", 9))
        if issue['original'] != issue['corrected']:
            self._populate_diff_view(text_view, issue['original'], issue['corrected'])
        else:
            text_view.setText(self.lang.get('corrector_suggestion_no_change'))
        layout.addWidget(text_view)

        action_layout = QHBoxLayout()

        if issue.get('type') == 'interactive':
            input_info = issue['input_request']
            input_label = QLabel(input_info['label'])
            input_field = QLineEdit()
            action_layout.addWidget(input_label)
            action_layout.addWidget(input_field, 1)
            issue['input_field'] = input_field

        action_layout.addStretch()

        if issue['type'] == 'suggestion':
            feature = issue.get("feature")
            if feature == "scope":
                button_text = self.lang.get('corrector_enable_scope_btn')
            elif feature == "lineno":
                button_text = self.lang.get('corrector_enable_lineno_btn')
            else:
                button_text = self.lang.get('corrector_acknowledge_btn')

            fix_button = QPushButton(button_text)
            fix_button.clicked.connect(lambda: self._handle_suggestion(issue))
        else:
            fix_button = QPushButton(self.lang.get('corrector_apply_fix_btn'))
            fix_button.clicked.connect(lambda: self._apply_fix(issue))

        issue['fix_button'] = fix_button
        action_layout.addWidget(fix_button)
        layout.addLayout(action_layout)
        return frame

    def _populate_diff_view(self, text_edit, original, corrected):
        lines = difflib.unified_diff(original.splitlines(), corrected.splitlines(), lineterm='', n=100)
        try:
            for _ in range(3): next(lines, None)
        except StopIteration:
            pass

        for line in lines:
            if line.startswith('+'):
                text_edit.setTextColor(QColor('#a7ffa7'))
                text_edit.append(line)
            elif line.startswith('-'):
                text_edit.setTextColor(QColor('#ff9f9f'))
                text_edit.append(line)
            else:
                text_edit.setTextColor(QColor('grey'))
                text_edit.append(line)

    def _apply_fix(self, issue):
        original_block = issue['original']
        corrected_block = issue['corrected']

        if issue.get('type') == 'interactive':
            input_field = issue['input_field']
            user_input = input_field.text().strip()
            if not (user_input.startswith('<') and user_input.endswith('>')):
                QMessageBox.warning(self, self.lang.get('patch_load_error_title'), self.lang.get('corrector_project_name_error'))
                return

            token = issue['input_request']['token_to_replace']
            corrected_block = original_block.replace(token, user_input, 1)

        self.corrected_patch = self.corrected_patch.replace(original_block, corrected_block)
        self.patch_was_modified = True

        issue['fix_button'].setText(self.lang.get('corrector_applied_btn'))
        issue['fix_button'].setEnabled(False)
        if issue.get('input_field'):
            issue['input_field'].setEnabled(False)

    def _handle_suggestion(self, issue):
        feature = issue.get("feature")
        qs = self.qs_widget
    
        if feature == "scope":
            qs.scope_checkbox.setChecked(True)
            qs.fuzzy_checkbox.setChecked(True) # Scope requires fuzzy
        elif feature == "lineno":
            qs.lineno_checkbox.setChecked(True)
        else:
            QMessageBox.information(self, self.lang.get('corrector_suggestion_title'), self.lang.get('corrector_suggestion_info'))
            issue['fix_button'].setText(self.lang.get('corrector_acknowledged_btn'))
            issue['fix_button'].setEnabled(False)
            return
    
        qs.save_quick_settings()
        QMessageBox.information(self, self.lang.get('corrector_feature_enabled_msg_title'), self.lang.get('corrector_feature_enabled_msg_text'))
        issue['fix_button'].setText(self.lang.get('corrector_applied_btn'))
        issue['fix_button'].setEnabled(False)

    def _apply_all_fixes(self):
        for issue in self.issues:
            if issue['fix_button'].isEnabled() and issue['type'] == 'syntax':
                self._apply_fix(issue)

    def get_corrected_patch(self):
        return self.corrected_patch, self.patch_was_modified