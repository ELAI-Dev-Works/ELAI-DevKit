import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QStackedWidget, QWidget
)
from PySide6.QtCore import Qt
from systems.security.crypto import CryptoPatterns

class FirstRunDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_win = parent
        self.context = parent.context
        self.lang = self.context.lang
        self.theme_manager = self.context.theme_manager
        self.settings_manager = self.context.settings_manager
        self.sm = self.context.security_manager

        self.setWindowTitle(self.lang.get('first_run_title', 'Welcome to ELAI-DevKit - First Run Setup'))
        self.resize(650, 480)
        self._init_ui()

        from systems.gui.utils.windows import center_window
        center_window(self, parent)

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # --- STEP 1: Appearance & Language ---
        step1_widget = QWidget()
        step1_layout = QVBoxLayout(step1_widget)

        self.title1 = QLabel(f"<h2>{self.lang.get('fr_step1_title', 'Step 1: Appearance & Language')}</h2>")
        self.desc1 = QLabel(self.lang.get('fr_step1_desc', 'Choose your preferred language and visual theme.'))
        step1_layout.addWidget(self.title1)
        step1_layout.addWidget(self.desc1)
        step1_layout.addSpacing(15)

        # Language
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(self.lang.get('language_label', 'Language:'))
        lang_layout.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        available_langs = self.lang.get_available_languages()
        self.lang_combo.addItems(available_langs)
        self.lang_combo.setCurrentText(self.lang.current_language)
        self.lang_combo.currentTextChanged.connect(self._on_lang_changed)
        lang_layout.addWidget(self.lang_combo)
        step1_layout.addLayout(lang_layout)

        # Theme
        theme_layout = QHBoxLayout()
        self.theme_label = QLabel(self.lang.get('theme_label', 'Theme:'))
        theme_layout.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.get_available_themes())
        self.theme_combo.setCurrentText(self.theme_manager.current_theme)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        step1_layout.addLayout(theme_layout)

        # Color Scheme
        color_layout = QHBoxLayout()
        self.color_label = QLabel(self.lang.get('color_scheme_label', 'Color Scheme:'))
        color_layout.addWidget(self.color_label)
        self.color_combo = QComboBox()
        self.color_combo.addItems(self.theme_manager.get_available_color_schemes())
        self.color_combo.setCurrentText(self.theme_manager.current_color_scheme)
        self.color_combo.currentTextChanged.connect(self._on_theme_changed)
        color_layout.addWidget(self.color_combo)
        step1_layout.addLayout(color_layout)

        step1_layout.addStretch()
        self.stack.addWidget(step1_widget)

        # --- STEP 2: Security Setup ---
        step2_widget = QWidget()
        step2_layout = QVBoxLayout(step2_widget)

        self.title2 = QLabel(f"<h2>{self.lang.get('fr_step2_title', 'Step 2: Security Setup')}</h2>")
        self.desc2 = QLabel(self.lang.get('fr_step2_desc', 'Set up a master password to secure your local sandbox and prevent unauthorized execution.'))
        self.desc2.setWordWrap(True)
        step2_layout.addWidget(self.title2)
        step2_layout.addWidget(self.desc2)
        step2_layout.addSpacing(15)

        p_layout = QHBoxLayout()
        self.p1_combo = QComboBox()
        self.p2_combo = QComboBox()
        for k, v in CryptoPatterns.PATTERNS.items():
            self.p1_combo.addItem(v, k)
            self.p2_combo.addItem(v, k)
        self.p2_combo.setCurrentIndex(1)

        p_layout.addWidget(QLabel("Encryption Pattern 1:"))
        p_layout.addWidget(self.p1_combo)
        p_layout.addWidget(QLabel("Pattern 2:"))
        p_layout.addWidget(self.p2_combo)
        step2_layout.addLayout(p_layout)

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setPlaceholderText("Enter a strong master password...")

        self.pwd_confirm = QLineEdit()
        self.pwd_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_confirm.setPlaceholderText("Confirm master password...")

        step2_layout.addWidget(QLabel("Master Password:"))
        step2_layout.addWidget(self.pwd_input)
        step2_layout.addWidget(self.pwd_confirm)
        step2_layout.addStretch()
        self.stack.addWidget(step2_widget)

        # --- ACTION BUTTONS ---
        btn_layout = QHBoxLayout()
        self.back_btn = QPushButton(self.lang.get('fr_btn_back', '< Back'))
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.hide()

        btn_layout.addStretch()

        self.next_btn = QPushButton(self.lang.get('fr_btn_next', 'Next >'))
        self.next_btn.clicked.connect(self._go_next)

        self.finish_btn = QPushButton(self.lang.get('fr_btn_finish', 'Finish Setup'))
        self.finish_btn.setStyleSheet("background-color: #23d18b; color: white; font-weight: bold; padding: 6px 12px;")
        self.finish_btn.clicked.connect(self._finish)
        self.finish_btn.hide()

        btn_layout.addWidget(self.back_btn)
        btn_layout.addWidget(self.next_btn)
        btn_layout.addWidget(self.finish_btn)

        layout.addLayout(btn_layout)

    def _on_lang_changed(self, text):
        if text:
            self.lang.set_language(text)
            if hasattr(self.parent_win, 'retranslate_ui'):
                self.parent_win.retranslate_ui()
            self._retranslate_local()

    def _on_theme_changed(self, text):
        color = self.color_combo.currentText()
        theme = self.theme_combo.currentText()
        if color and theme:
            self.theme_manager.apply_theme(color, theme)

    def _retranslate_local(self):
        self.setWindowTitle(self.lang.get('first_run_title', 'Welcome to ELAI-DevKit - First Run Setup'))
        self.title1.setText(f"<h2>{self.lang.get('fr_step1_title', 'Step 1: Appearance & Language')}</h2>")
        self.desc1.setText(self.lang.get('fr_step1_desc', 'Choose your preferred language and visual theme.'))
        self.title2.setText(f"<h2>{self.lang.get('fr_step2_title', 'Step 2: Security Setup')}</h2>")
        self.desc2.setText(self.lang.get('fr_step2_desc', 'Set up a master password to secure your local sandbox and prevent unauthorized execution.'))
        self.lang_label.setText(self.lang.get('language_label', 'Language:'))
        self.theme_label.setText(self.lang.get('theme_label', 'Theme:'))
        self.color_label.setText(self.lang.get('color_scheme_label', 'Color Scheme:'))
        self.back_btn.setText(self.lang.get('fr_btn_back', '< Back'))
        self.next_btn.setText(self.lang.get('fr_btn_next', 'Next >'))
        self.finish_btn.setText(self.lang.get('fr_btn_finish', 'Finish Setup'))

    def _go_back(self):
        self.stack.setCurrentIndex(0)
        self.back_btn.hide()
        self.finish_btn.hide()
        self.next_btn.show()

    def _go_next(self):
        core_settings = self.settings_manager.get_setting(['core'], {})
        core_settings['language'] = self.lang_combo.currentText()
        if 'theme' not in core_settings:
            core_settings['theme'] = {}
        core_settings['theme']['theme'] = self.theme_combo.currentText()
        core_settings['theme']['color_scheme'] = self.color_combo.currentText()
        self.settings_manager.update_setting(['core'], core_settings)
        self.settings_manager.save_settings_file()

        self.stack.setCurrentIndex(1)
        self.back_btn.show()
        self.next_btn.hide()
        self.finish_btn.show()

    def _finish(self):
        pwd = self.pwd_input.text()
        conf = self.pwd_confirm.text()

        if not pwd:
            QMessageBox.warning(self, "Error", self.lang.get('fr_pwd_empty', 'Password cannot be empty.'))
            return
        if pwd != conf:
            QMessageBox.warning(self, "Error", self.lang.get('fr_pwd_mismatch', 'Passwords do not match.'))
            return

        p1 = self.p1_combo.currentData()
        p2 = self.p2_combo.currentData()

        self.sm.setup(pwd, p1, p2)
        QMessageBox.information(self, "Success", "Security setup complete! Welcome to ELAI-DevKit.")
        self.accept()

    def closeEvent(self, event):
        if not self.sm.is_setup:
            QMessageBox.critical(self, "Error", self.lang.get('fr_warning_incomplete', 'You must complete the setup to use ELAI-DevKit.'))
            event.ignore()
        else:
            super().closeEvent(event)