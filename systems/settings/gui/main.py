import tomllib
from PySide6.QtWidgets import (
    QPushButton, QVBoxLayout, QFrame, QHBoxLayout,
    QSpacerItem, QSizePolicy, QLabel, QComboBox, QFormLayout,
    QGroupBox, QTabWidget, QWidget, QCheckBox
)
from PySide6.QtCore import Signal
from systems.settings.defaults import main_default_settings

class SettingsPanel(QFrame):
    closed = Signal()

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.lang = main_window.lang
        self.setObjectName("settingsOverlay")
        self.state_on_open = {}
        self.defaults = main_default_settings
        self.init_ui()

    def init_ui(self):
        overlay_layout = QHBoxLayout(self)
        overlay_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        content_box = QFrame()
        content_box.setObjectName("settingsContentBox")
        content_box.setMinimumWidth(600)
        layout = QVBoxLayout(content_box)
        layout.setContentsMargins(15, 15, 15, 15)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget, 1)

        main_settings_widget = self._create_main_settings_tab()
        ui_settings_widget = self._create_ui_settings_tab()

        self.tab_widget.addTab(main_settings_widget, "Main")
        self.tab_widget.addTab(ui_settings_widget, "UI")

        button_layout = self._create_control_buttons()
        layout.addLayout(button_layout)

        overlay_layout.addWidget(content_box)
        overlay_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

    def _create_main_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.general_group = QGroupBox()
        form_layout = QFormLayout(self.general_group)

        self.lang_combo = QComboBox()
        self.lang_combo.currentIndexChanged.connect(self.preview_language_change)
        self.lang_label_ref = QLabel()
        form_layout.addRow(self.lang_label_ref, self.lang_combo)

        self.theme_combo = QComboBox()
        self.theme_combo.currentIndexChanged.connect(self.preview_theme_change)
        self.theme_label_ref = QLabel()
        form_layout.addRow(self.theme_label_ref, self.theme_combo)

        self.color_scheme_combo = QComboBox()
        self.color_scheme_combo.currentIndexChanged.connect(self.preview_color_scheme_change)
        self.color_scheme_label_ref = QLabel()
        form_layout.addRow(self.color_scheme_label_ref, self.color_scheme_combo)

        layout.addWidget(self.general_group)
        layout.addStretch()
        return widget

    def _create_ui_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.ui_group = QGroupBox()
        form_layout = QFormLayout(self.ui_group)

        self.always_show_tooltips_checkbox = QCheckBox()
        self.always_show_tooltips_checkbox.setStyleSheet("border: none; background: transparent;")
        form_layout.addRow(self.always_show_tooltips_checkbox)

        from PySide6.QtWidgets import QSpinBox
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        self.font_size_spinbox.setSuffix(" pt")
        self.font_size_label = QLabel()
        form_layout.addRow(self.font_size_label, self.font_size_spinbox)

        layout.addWidget(self.ui_group)
        layout.addStretch()
        return widget

    def _create_control_buttons(self):
        button_layout = QHBoxLayout()
        self.reset_button = QPushButton()
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()

        self.apply_button = QPushButton()
        self.apply_button.clicked.connect(self.apply_settings)

        self.save_project_button = QPushButton()
        self.save_project_button.clicked.connect(lambda: self.save_settings(is_project=True))

        self.save_button = QPushButton()
        self.save_button.clicked.connect(lambda: self.save_settings(is_project=False))

        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.close_and_revert)
        self.close_button.setDefault(True)

        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.save_project_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)
        return button_layout

    def retranslate_ui(self):
        lang = self.main_window.lang
        self.tab_widget.setTabText(0, lang.get('settings_main_tab'))
        self.tab_widget.setTabText(1, lang.get('settings_ui_tab'))

        self.ui_group.setTitle(lang.get('settings_ui_group_title'))
        self.always_show_tooltips_checkbox.setText(lang.get('ui_always_show_tooltips'))
        self.always_show_tooltips_checkbox.setToolTip(lang.get('ui_always_show_tooltips_tooltip'))
        if hasattr(self, 'font_size_label'):
            self.font_size_label.setText(lang.get('ui_font_size', 'Global Font Size:'))

        self.general_group.setTitle(lang.get('settings_general_group_title'))
        self.lang_label_ref.setText(lang.get('language_label'))
        self.theme_label_ref.setText(lang.get('theme_label'))
        self.color_scheme_label_ref.setText(lang.get('color_scheme_label', 'Color Scheme:'))

        self.reset_button.setText(lang.get('reset_btn')).addGUITooltip(lang.get('settings_reset_tooltip'))
        self.apply_button.setText(lang.get('apply_btn')).addGUITooltip(lang.get('settings_apply_tooltip'))

        self.save_project_button.setText(lang.get('save_project_btn', 'Save for Current Project'))
        self.save_project_button.setEnabled(bool(self.main_window.root_path))

        self.save_button.setText(lang.get('save_btn')).addGUITooltip(lang.get('settings_save_tooltip'))
        self.close_button.setText(lang.get('close_btn')).addGUITooltip(lang.get('settings_close_tooltip'))

    def populate_languages(self, current_lang_code):
        self.lang_combo.blockSignals(True)
        self.lang_combo.clear()
        available_langs = self.main_window.lang.get_available_languages()
        for lang_code in available_langs:
            self.lang_combo.addItem(lang_code)
        if current_lang_code in available_langs:
            self.lang_combo.setCurrentText(current_lang_code)
        self.lang_combo.blockSignals(False)

    def store_initial_state(self):
        tm = self.main_window.theme_manager

        if not hasattr(self, 'state_on_open') or not self.state_on_open:
            self.state_on_open = {}

        self.state_on_open['language'] = self.main_window.lang.current_language
        if 'theme' not in self.state_on_open:
            self.state_on_open['theme'] = {}
        self.state_on_open['theme']['theme'] = tm.current_theme
        self.state_on_open['theme']['color_scheme'] = tm.current_color_scheme

        if 'ui' not in self.state_on_open:
            self.state_on_open['ui'] = {}
        self.state_on_open['ui']['always_show_tooltips'] = self.always_show_tooltips_checkbox.isChecked() if hasattr(self, 'always_show_tooltips_checkbox') else False
        self.state_on_open['ui']['font_size'] = self.font_size_spinbox.value() if hasattr(self, 'font_size_spinbox') else 10

        self.populate_languages(self.state_on_open.get('language', 'en'))

        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self.theme_combo.addItems(tm.get_available_themes())
        self.theme_combo.setCurrentText(tm.current_theme)
        self.theme_combo.blockSignals(False)

        self.color_scheme_combo.blockSignals(True)
        self.color_scheme_combo.clear()
        self.color_scheme_combo.addItems(tm.get_available_color_schemes())
        self.color_scheme_combo.setCurrentText(tm.current_color_scheme)
        self.color_scheme_combo.blockSignals(False)

        ui_settings = self.state_on_open.get('ui', {})
        self.always_show_tooltips_checkbox.setChecked(ui_settings.get('always_show_tooltips', False))
        if hasattr(self, 'font_size_spinbox'):
            self.font_size_spinbox.setValue(ui_settings.get('font_size', 10))

    def preview_language_change(self):
        if self.lang_combo.count() > 0 and self.lang_combo.currentText():
            self.main_window.apply_main_settings({'language': self.lang_combo.currentText()})
            self.retranslate_ui()

    def preview_theme_change(self):
        if self.theme_combo.count() > 0 and self.theme_combo.currentText():
            self.main_window.theme_manager.apply_theme(
                self.main_window.theme_manager.current_color_scheme,
                self.theme_combo.currentText()
            )

    def preview_color_scheme_change(self):
        if self.color_scheme_combo.count() > 0 and self.color_scheme_combo.currentText():
            self.main_window.theme_manager.apply_theme(
                self.color_scheme_combo.currentText(),
                self.main_window.theme_manager.current_theme
            )

    def apply_settings(self):
        self.state_on_open['language'] = self.lang_combo.currentText()
        if 'theme' not in self.state_on_open:
            self.state_on_open['theme'] = {}
        self.state_on_open['theme']['theme'] = self.theme_combo.currentText()
        self.state_on_open['theme']['color_scheme'] = self.color_scheme_combo.currentText()

        if 'ui' not in self.state_on_open:
            self.state_on_open['ui'] = {}
        self.state_on_open['ui']['always_show_tooltips'] = self.always_show_tooltips_checkbox.isChecked()
        self.state_on_open['ui']['font_size'] = self.font_size_spinbox.value()
        self.main_window.apply_main_settings(self.state_on_open)

    def save_settings(self, is_project=False):
        self.apply_settings()
        sm = self.main_window.settings_manager
        core_settings = self.state_on_open.copy()

        # Preserve existing extension settings since they are now managed in ExtensionsWindow
        if is_project:
            existing_core = sm.load_project_settings().get('core', {})
        else:
            existing_core = sm.load_settings_file().get('core', {})

        if 'extensions' in existing_core:
            core_settings['extensions'] = existing_core['extensions']

        sm.update_setting(['core'], core_settings, is_project)
        if is_project:
            sm.save_project_settings()
            if hasattr(self.main_window, 'patcher_log_output'):
                self.main_window.patcher_log_output.appendPlainText(self.lang.get('project_settings_saved_log', '[Settings] Project settings saved successfully.'))
        else:
            sm.save_settings_file()
            if hasattr(self.main_window, 'patcher_log_output'):
                self.main_window.patcher_log_output.appendPlainText(self.lang.get('settings_saved_log'))

    def close_and_revert(self):
        if not self.state_on_open:
            self.store_initial_state()

        self.main_window.lang.set_language(self.state_on_open.get('language', 'en'))
        theme_settings = self.state_on_open.get('theme', {})

        # New format only: color_scheme + theme
        color_scheme = theme_settings.get('color_scheme', 'dark')
        theme = theme_settings.get('theme', 'sleek')

        # Validate color_scheme
        available_colors = self.main_window.theme_manager.get_available_color_schemes()
        if color_scheme not in available_colors:
            color_scheme = 'dark'
        
        # Validate theme
        available_themes = self.main_window.theme_manager.get_available_themes()
        if theme not in available_themes:
            theme = 'sleek'

        self.main_window.theme_manager.apply_theme(color_scheme, theme)
        self.main_window.retranslate_ui()
        self.closed.emit()

    def reset_to_defaults(self):
        core_defaults = self.defaults.get('core', {})
        theme_defaults = core_defaults.get('theme', {})
        lang_default = core_defaults.get('language', 'en')

        self.main_window.lang.set_language(lang_default)
        self.main_window.theme_manager.apply_theme(
            theme_defaults.get('color_scheme', 'dark'),
            theme_defaults.get('theme', 'clean')
        )
        self.main_window.retranslate_ui()

        self.populate_languages(lang_default)
        self.theme_combo.setCurrentText(theme_defaults.get('theme', 'clean'))
        self.color_scheme_combo.setCurrentText(theme_defaults.get('color_scheme', 'dark'))

        ui_defaults = core_defaults.get('ui', {})
        self.always_show_tooltips_checkbox.setChecked(ui_defaults.get('always_show_tooltips', False))
        if hasattr(self, 'font_size_spinbox'):
            self.font_size_spinbox.setValue(ui_defaults.get('font_size', 10))