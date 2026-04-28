from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QDialogButtonBox, QPlainTextEdit,
    QGroupBox, QLabel, QTabWidget, QWidget, QCheckBox
)

class IgnoreSettingsWindow(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.lang = main_window.lang
        self.settings_manager = main_window.settings_manager
        self.setWindowTitle(self.lang.get('ignore_settings_title'))
        self.setMinimumSize(600, 500)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # --- Tab 1: Global ---
        self.global_tab = QWidget()
        self.global_dirs_edit, self.global_files_edit = self._create_editor_layout(self.global_tab)
        self.tabs.addTab(self.global_tab, self.lang.get('ignore_tab_global'))

        # --- Tab 2: Temporary ---
        self.temp_tab = QWidget()
        self.temp_dirs_edit, self.temp_files_edit = self._create_editor_layout(self.temp_tab)
        self.tabs.addTab(self.temp_tab, self.lang.get('ignore_tab_temp'))

        # --- Tab 3: Current Project ---
        self.project_tab = QWidget()
        self.project_dirs_edit, self.project_files_edit = self._create_editor_layout(self.project_tab)
        self.tabs.addTab(self.project_tab, self.lang.get('ignore_tab_project', 'Current Project List'))
        self.project_tab.setEnabled(bool(self.main_window.root_path))

        # --- Bottom Options ---
        self.gitignore_checkbox = QCheckBox(self.lang.get('ignore_use_gitignore'))
        self.gitignore_checkbox.addGUITooltip(self.lang.get('ignore_use_gitignore_tooltip'))
        layout.addWidget(self.gitignore_checkbox)

        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self._save_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _create_editor_layout(self, parent_widget):
        layout = QVBoxLayout(parent_widget)

        instruction_layout = QHBoxLayout()
        instruction_layout.setContentsMargins(0, 0, 0, 0)
        instructions = QLabel(self.lang.get('ignore_settings_tags_label', 'Instruction:'), parent_widget)
        instructions.setStyleSheet("color: #aaa; font-style: italic; margin-bottom: 5px;")
        instructions.addGUITooltip(self.lang.get('ignore_settings_tags_info'))
        instruction_layout.addWidget(instructions)
        instruction_layout.addStretch()
        layout.addLayout(instruction_layout)

        dirs_group = QGroupBox(self.lang.get('ignore_dirs_label'))
        dirs_layout = QVBoxLayout(dirs_group)
        dirs_info = QLabel(self.lang.get('ignore_settings_dirs_info'))
        dirs_info.setWordWrap(True)
        dirs_edit = QPlainTextEdit()
        dirs_layout.addWidget(dirs_info)
        dirs_layout.addWidget(dirs_edit)
        layout.addWidget(dirs_group)

        files_group = QGroupBox(self.lang.get('ignore_files_label'))
        files_layout = QVBoxLayout(files_group)
        files_info = QLabel(self.lang.get('ignore_settings_files_info'))
        files_info.setWordWrap(True)
        files_edit = QPlainTextEdit()
        files_layout.addWidget(files_info)
        files_layout.addWidget(files_edit)
        layout.addWidget(files_group)

        return dirs_edit, files_edit

    def _load_data(self):
        # Global & Project
        g_dirs, g_files, use_git, p_dirs, p_files = self.settings_manager.get_ignore_lists()
        self.global_dirs_edit.setPlainText('\n'.join(g_dirs))
        self.global_files_edit.setPlainText('\n'.join(g_files))
        self.gitignore_checkbox.setChecked(use_git)

        self.project_dirs_edit.setPlainText('\n'.join(p_dirs))
        self.project_files_edit.setPlainText('\n'.join(p_files))

        # Temporary (from MainWindow)
        t_dirs = getattr(self.main_window, 'temp_ignore_dirs',[])
        t_files = getattr(self.main_window, 'temp_ignore_files',[])
        self.temp_dirs_edit.setPlainText('\n'.join(t_dirs))
        self.temp_files_edit.setPlainText('\n'.join(t_files))

    def _save_and_accept(self):
        # 1. Save Global
        g_dirs =[l.strip() for l in self.global_dirs_edit.toPlainText().splitlines() if l.strip()]
        g_files =[l.strip() for l in self.global_files_edit.toPlainText().splitlines() if l.strip()]

        settings_to_save = {
            'dirs': g_dirs,
            'files': g_files,
            'use_gitignore': self.gitignore_checkbox.isChecked()
        }
        self.settings_manager.update_setting(['core', 'ignore'], settings_to_save)
        self.settings_manager.save_settings_file()

        # 2. Save Project
        if self.main_window.root_path:
            p_dirs =[l.strip() for l in self.project_dirs_edit.toPlainText().splitlines() if l.strip()]
            p_files =[l.strip() for l in self.project_files_edit.toPlainText().splitlines() if l.strip()]
            p_settings = {'dirs': p_dirs, 'files': p_files}
            self.settings_manager.update_setting(['core', 'project_ignore'], p_settings, is_project=True)
            self.settings_manager.save_project_settings()

        # 3. Save Temporary (to MainWindow memory)
        t_dirs = [l.strip() for l in self.temp_dirs_edit.toPlainText().splitlines() if l.strip()]
        t_files = [l.strip() for l in self.temp_files_edit.toPlainText().splitlines() if l.strip()]

        self.main_window.temp_ignore_dirs = t_dirs
        self.main_window.temp_ignore_files = t_files

        self.accept()

def get_quick_settings():
    """
    Returns a list of quick setting definitions for the core GUI.
    """
    return [
        {
            'id': 'core_ignore_list',
            'qs_type': 'window',
            'title': 'Ignore Lists',
            'widget_class': IgnoreSettingsWindow
        }
    ]