import tomllib
import os
import subprocess
from systems.gui.icons import IconManager
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QCheckBox,
    QFormLayout, QSpinBox, QLabel, QPushButton, QSpacerItem, QSizePolicy,
    QComboBox, QLineEdit, QMessageBox, QDialog, QTextEdit, QDialogButtonBox
)
from apps.dev_patcher.core.restore import get_available_backups, restore_backup
from apps.dev_patcher.core.backup import create_backup as core_create_backup, create_git_backup
from apps.dev_patcher.gui.windows.restore_backup import RestoreBackupDialog

default_settings = """
[Features]
fuzzy_matching = true
scope_matching = true
precise_patching = false
similarity_threshold = 85

[Backup]
method = "zip"
commit_message = "Auto-backup before patching"
"""

class DevPatcherQuickSettingsWidget(QWidget):
    def __init__(self, context):
        super().__init__()
        self.main_window = context.main_window
        self.lang = context.lang
        self.settings_manager = context.settings_manager
        self.defaults = tomllib.loads(default_settings)

        self._create_settings_widgets()
        self.init_ui()
        self.load_settings()
        self.retranslate_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)

        features_h_layout = QHBoxLayout()
        features_h_layout.addWidget(self.experimental_group)
        features_h_layout.addWidget(self.additional_features_group)
        layout.addLayout(features_h_layout)


        backup_layout = QHBoxLayout()
        self.backup_method_label = QLabel()
        backup_layout.addWidget(self.backup_method_label)
        backup_layout.addWidget(self.backup_method_combo)
        backup_layout.addWidget(self.backup_commit_msg)
        backup_layout.addWidget(self.backup_msg_maximize_btn)
        backup_layout.addWidget(self.init_git_btn)
        backup_layout.addStretch()
        layout.addLayout(backup_layout)

        # Populate backup method combo with default items
        self.backup_method_combo.addItem("None", "none")
        self.backup_method_combo.addItem("ZIP Archive", "zip")
        self.backup_method_combo.addItem("Git Commit", "git")
        self.backup_method_combo.addItem("Both (ZIP + Git)", "all")

        self.backup_method_combo.currentIndexChanged.connect(self._update_git_ui_state)
        self.init_git_btn.clicked.connect(self._init_git_repo)

        restore_layout = QVBoxLayout(self.restore_group)
        restore_h_layout = QHBoxLayout()
        restore_h_layout.addWidget(self.restore_refresh_btn)
        restore_h_layout.addWidget(self.manual_backup_btn)
        restore_h_layout.addWidget(self.restore_combo, 1)
        restore_h_layout.addWidget(self.restore_mode_combo)
        restore_h_layout.addWidget(self.restore_btn)
        restore_h_layout.addWidget(self.restore_all_btn)
        restore_layout.addLayout(restore_h_layout)
        layout.addWidget(self.restore_group)

        self.restore_refresh_btn.clicked.connect(self._refresh_restore_list)
        self.manual_backup_btn.clicked.connect(self._manual_backup)
        self.backup_msg_maximize_btn.clicked.connect(self._maximize_commit_msg)
        self.restore_btn.clicked.connect(self._on_restore_clicked)
        self.restore_all_btn.clicked.connect(self._open_restore_modal)


        qs_button_layout = QHBoxLayout()
        qs_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.qs_reset_button = QPushButton()
        self.qs_apply_button = QPushButton()
        self.qs_save_project_button = QPushButton()
        self.qs_save_button = QPushButton()
        self.qs_reset_button.clicked.connect(self.reset_quick_settings)
        self.qs_apply_button.clicked.connect(self.apply_quick_settings)
        self.qs_save_project_button.clicked.connect(lambda: self.save_quick_settings(is_project=True))
        self.qs_save_button.clicked.connect(lambda: self.save_quick_settings(is_project=False))
        qs_button_layout.addWidget(self.qs_reset_button)
        qs_button_layout.addWidget(self.qs_apply_button)
        qs_button_layout.addWidget(self.qs_save_project_button)
        qs_button_layout.addWidget(self.qs_save_button)
        layout.addLayout(qs_button_layout)

    def _create_settings_widgets(self):
        self.experimental_group = QGroupBox()
        experimental_layout = QVBoxLayout()
        self.lineno_checkbox = QCheckBox()
        experimental_layout.addWidget(self.lineno_checkbox)
        self.experimental_group.setLayout(experimental_layout)

        self.additional_features_group = QGroupBox()
        form_layout = QFormLayout(self.additional_features_group)
        self.fuzzy_checkbox = QCheckBox()
        self.scope_checkbox = QCheckBox()
        form_layout.addRow(self.fuzzy_checkbox)
        form_layout.addRow(self.scope_checkbox)

        self.similarity_spinbox = QSpinBox()
        self.similarity_spinbox.setRange(1, 100)
        self.similarity_spinbox.setSuffix(" %")
        self.similarity_label = QLabel()
        form_layout.addRow(self.similarity_label, self.similarity_spinbox)


        self.backup_method_combo = QComboBox()
        self.backup_commit_msg = QLineEdit()
        self.init_git_btn = QPushButton()

        self.backup_msg_maximize_btn = QPushButton()
        self.backup_msg_maximize_btn.setFixedSize(24, 24)
        self.backup_msg_maximize_btn.setStyleSheet("padding: 2px;")
        self.backup_msg_maximize_btn.setProperty("no_custom_tooltip", True)

        self.restore_group = QGroupBox()
        self.manual_backup_btn = QPushButton()
        self.restore_refresh_btn = QPushButton()
        self.restore_refresh_btn.setFixedSize(32, 32)
        self.restore_refresh_btn.setStyleSheet("padding: 5px;")
        self.restore_refresh_btn.setProperty("no_custom_tooltip", True)
        self.restore_combo = QComboBox()
        self.restore_mode_combo = QComboBox()
        self.restore_btn = QPushButton()
        self.restore_all_btn = QPushButton()


    def _update_git_ui_state(self):
        method = self.backup_method_combo.currentData()
        if method in['git', 'all']:
            if self.main_window.root_path:
                if os.path.exists(os.path.join(self.main_window.root_path, '.git')):
                    self.backup_commit_msg.setVisible(True)
                    self.backup_msg_maximize_btn.setVisible(True)
                    self.init_git_btn.setVisible(False)
                else:
                    self.backup_commit_msg.setVisible(False)
                    self.backup_msg_maximize_btn.setVisible(False)
                    self.init_git_btn.setVisible(True)
            else:
                self.backup_commit_msg.setVisible(True)
                self.backup_msg_maximize_btn.setVisible(True)
                self.init_git_btn.setVisible(False)
        else:
            self.backup_commit_msg.setVisible(False)
            self.backup_msg_maximize_btn.setVisible(False)
            self.init_git_btn.setVisible(False)

    def _init_git_repo(self):
        if self.main_window.root_path:
            try:
                subprocess.run(["git", "init"], cwd=self.main_window.root_path, capture_output=True, text=True, check=True)
                self._update_git_ui_state()
                self.main_window.patcher_log_output.appendPlainText(self.lang.get('git_init_success_log'))
            except Exception as e:
                QMessageBox.critical(self, self.lang.get('patch_load_error_title'), self.lang.get('git_init_failed_msg').format(e))


    def _manual_backup(self):
        if not self.main_window.root_path:
            QMessageBox.warning(self, self.lang.get('patch_load_error_title', 'Error'), self.lang.get('project_folder_missing_error', 'Project folder not selected.'))
            return

        method = self.backup_method_combo.currentData()
        if method in['none', None]:
            QMessageBox.information(self, "Backup", "Backup method is set to None.")
            return

        ignore_dirs, ignore_files = [],[]
        if hasattr(self.main_window, 'get_combined_ignore_lists'):
            ignore_dirs, ignore_files = self.main_window.get_combined_ignore_lists()

        commit_msg = self.backup_commit_msg.text() or "Manual backup"
        target_name = self.lang.get('project_target_name', 'project')

        success_any = False
        if method in ['zip', 'all']:
            self.main_window.patcher_log_output.appendPlainText(self.lang.get('backup_creation_log', 'Creating backup of the {}...').format(target_name))
            succ, msg = core_create_backup(self.main_window.root_path, ignore_dirs, ignore_files)
            if succ:
                self.main_window.patcher_log_output.appendPlainText(self.lang.get('backup_success_log', 'Backup successfully created: {}').format(msg))
                success_any = True
            else:
                QMessageBox.critical(self, self.lang.get('patch_load_error_title', 'Error'), self.lang.get('backup_failed_error_msg', 'Failed to create backup of the {}: {}').format(target_name, msg))

        if method in ['git', 'all']:
            self.main_window.patcher_log_output.appendPlainText(self.lang.get('backup_git_creation_log', 'Creating git commit for {}...').format(target_name))
            succ, msg = create_git_backup(self.main_window.root_path, commit_msg, ignore_dirs, ignore_files)
            if succ:
                self.main_window.patcher_log_output.appendPlainText(self.lang.get('backup_git_success_log', 'Git commit successfully created: {}').format(msg))
                success_any = True
            else:
                QMessageBox.critical(self, self.lang.get('patch_load_error_title', 'Error'), self.lang.get('backup_git_failed_error_msg', 'Failed to create git commit for {}: {}').format(target_name, msg))

        if success_any:
            self._refresh_restore_list()

    def _maximize_commit_msg(self):
        from systems.gui.utils.windows import center_window
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lang.get('commit_msg_dialog_title', 'Commit Message'))
        dialog.resize(400, 300)
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setPlainText(self.backup_commit_msg.text())
        layout.addWidget(text_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        center_window(dialog, self.main_window)

        if dialog.exec():
            text = text_edit.toPlainText().replace('\n', ' ').strip()
            self.backup_commit_msg.setText(text)

    def _refresh_restore_list(self):
        self.restore_combo.clear()
        if not self.main_window.root_path:
            return
        method = self.backup_method_combo.currentData() or 'all'
        backups = get_available_backups(self.main_window.root_path, method)
        for b in backups[:5]:
            self.restore_combo.addItem(b['display'], b)

    def _on_restore_clicked(self):
        if not self.main_window.root_path: return
        b_info = self.restore_combo.currentData()
        if not b_info: return
        mode = self.restore_mode_combo.currentData()
        reply = QMessageBox.question(self, self.lang.get('restore_modal_title', 'Restore'), self.lang.get('restore_confirm_msg', 'Are you sure you want to restore?'), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            succ, msg = restore_backup(self.main_window.root_path, b_info, mode)
            if succ:
                self.main_window.patcher_log_output.appendPlainText(self.lang.get('restore_success_msg', 'Restore success'))
                QMessageBox.information(self, self.lang.get('restore_modal_title', 'Restore'), self.lang.get('restore_success_msg', 'Restore success'))
            else:
                self.main_window.patcher_log_output.appendPlainText(self.lang.get('restore_error_msg', 'Restore failed: {}').format(msg))
                QMessageBox.critical(self, self.lang.get('restore_modal_title', 'Restore'), self.lang.get('restore_error_msg', 'Restore failed: {}').format(msg))

    def _open_restore_modal(self):
        if not self.main_window.root_path: return
        method = self.backup_method_combo.currentData() or 'all'
        backups = get_available_backups(self.main_window.root_path, method)
        dialog = RestoreBackupDialog(self.main_window, backups, self.restore_mode_combo.currentData())
        if dialog.exec():
            b_info, mode = dialog.get_selected()
            if b_info:
                succ, msg = restore_backup(self.main_window.root_path, b_info, mode)
                if succ:
                    self.main_window.patcher_log_output.appendPlainText(self.lang.get('restore_success_msg', 'Restore success'))
                    QMessageBox.information(self, self.lang.get('restore_modal_title', 'Restore'), self.lang.get('restore_success_msg', 'Restore success'))
                else:
                    self.main_window.patcher_log_output.appendPlainText(self.lang.get('restore_error_msg', 'Restore failed: {}').format(msg))
                    QMessageBox.critical(self, self.lang.get('restore_modal_title', 'Restore'), self.lang.get('restore_error_msg', 'Restore failed: {}').format(msg))


    def project_folder_changed(self, root_path):
        self.qs_save_project_button.setEnabled(bool(root_path))
        self._update_git_ui_state()
        self._refresh_restore_list()

    def load_settings(self):
        settings_path = ['apps', 'dev_patcher', 'quick']
        all_settings = self.settings_manager.get_setting(settings_path, self.defaults)

        features = all_settings.get('Features', {})
        backup = all_settings.get('Backup', {})

        self.fuzzy_checkbox.setChecked(features.get('fuzzy_matching', False))
        self.scope_checkbox.setChecked(features.get('scope_matching', False))
        self.lineno_checkbox.setChecked(features.get('precise_patching', False))
        self.similarity_spinbox.setValue(int(features.get('similarity_threshold', 85)))

        method = backup.get('method', 'zip')
        if isinstance(method, bool):
            method = 'zip' if method else 'none'
        elif 'enabled' in backup and 'method' not in backup:
            method = 'zip' if backup['enabled'] else 'none'

        idx = self.backup_method_combo.findData(method)
        if idx >= 0:
            self.backup_method_combo.setCurrentIndex(idx)

        self.backup_commit_msg.setText(backup.get('commit_message', 'Auto-backup before patching'))
        self._update_git_ui_state()
        self._refresh_restore_list()

    def _get_current_settings(self):
        return {
            'Features': {
                'fuzzy_matching': self.fuzzy_checkbox.isChecked(),
                'scope_matching': self.scope_checkbox.isChecked(),
                'precise_patching': self.lineno_checkbox.isChecked(),
                'similarity_threshold': self.similarity_spinbox.value(),
            },
            'Backup': {
                'method': self.backup_method_combo.currentData(),
                'commit_message': self.backup_commit_msg.text()
            }
        }

    def apply_quick_settings(self):
        self.settings_manager.update_setting(['apps', 'dev_patcher', 'quick'], self._get_current_settings())
        self.main_window.patcher_log_output.appendPlainText(self.lang.get('quick_settings_applied_log', '[Settings] Quick settings applied.'))
        self._refresh_restore_list()

    def save_quick_settings(self, is_project=False):
        self.settings_manager.update_setting(['apps', 'dev_patcher', 'quick'], self._get_current_settings(), is_project)
        if is_project:
            self.settings_manager.save_project_settings()
            self.main_window.patcher_log_output.appendPlainText(self.lang.get('quick_settings_project_saved_log', '[Settings] Project quick settings saved.'))
        else:
            self.settings_manager.save_settings_file()
            self.main_window.patcher_log_output.appendPlainText(self.lang.get('quick_settings_saved_log'))
        self._refresh_restore_list()

    def reset_quick_settings(self):
        features = self.defaults.get('Features', {})
        backup = self.defaults.get('Backup', {})

        self.fuzzy_checkbox.setChecked(features.get('fuzzy_matching', False))
        self.scope_checkbox.setChecked(features.get('scope_matching', False))
        self.lineno_checkbox.setChecked(features.get('precise_patching', False))
        self.similarity_spinbox.setValue(int(features.get('similarity_threshold', 85)))

        method = backup.get('method', 'zip')
        idx = self.backup_method_combo.findData(method)
        if idx >= 0:
            self.backup_method_combo.setCurrentIndex(idx)
        self.backup_commit_msg.setText(backup.get('commit_message', 'Auto-backup before patching'))
        self._update_git_ui_state()

        self.main_window.patcher_log_output.appendPlainText(self.lang.get('quick_settings_reset_log'))

    def retranslate_ui(self):
        self.lineno_checkbox.setText(self.lang.get('precise_patching_checkbox')).addGUITooltip(self.lang.get('precise_patching_tooltip'))
        self.fuzzy_checkbox.setText(self.lang.get('fuzzy_matching_checkbox')).addGUITooltip(self.lang.get('fuzzy_matching_tooltip'))
        self.scope_checkbox.setText(self.lang.get('scope_matching_checkbox')).addGUITooltip(self.lang.get('scope_matching_tooltip'))
        self.similarity_spinbox.setToolTip(self.lang.get('similarity_threshold_tooltip'))

        self.experimental_group.setTitle(self.lang.get('experimental_group_title'))
        self.lineno_checkbox.setText(self.lang.get('precise_patching_checkbox'))
        self.additional_features_group.setTitle(self.lang.get('additional_features_group_title'))
        self.fuzzy_checkbox.setText(self.lang.get('fuzzy_matching_checkbox'))
        self.scope_checkbox.setText(self.lang.get('scope_matching_checkbox'))
        self.similarity_label.setText(self.lang.get('similarity_threshold_label'))

        self.backup_method_label.setText(self.lang.get('backup_method_label'))
        self.backup_commit_msg.setPlaceholderText(self.lang.get('backup_commit_msg_placeholder'))
        self.init_git_btn.setText(self.lang.get('init_git_btn'))

        self.manual_backup_btn.setText(self.lang.get('manual_backup_btn', 'Manual')).addGUITooltip(self.lang.get('manual_backup_tooltip', 'Manually trigger a backup based on current settings.'))
        self.backup_msg_maximize_btn.setToolTip(self.lang.get('commit_msg_maximize_tooltip', 'Edit long commit message'))

        p = self.main_window.theme_manager.current_palette if hasattr(self.main_window, 'theme_manager') else {}
        icon_color = p.get("icon_default", "#e0e0e0")
        self.backup_msg_maximize_btn.setIcon(IconManager.get_icon("core.maximize", icon_color))

        # Update backup method combo texts while preserving selection
        current_data = self.backup_method_combo.currentData()
        self.backup_method_combo.blockSignals(True)
        self.backup_method_combo.setItemText(0, self.lang.get('backup_method_none'))
        self.backup_method_combo.setItemText(1, self.lang.get('backup_method_zip'))
        self.backup_method_combo.setItemText(2, self.lang.get('backup_method_git'))
        self.backup_method_combo.setItemText(3, self.lang.get('backup_method_all'))
        
        # Restore selection if needed
        if current_data:
            idx = self.backup_method_combo.findData(current_data)
            if idx >= 0:
                self.backup_method_combo.setCurrentIndex(idx)
        self.backup_method_combo.blockSignals(False)

        self.restore_group.setTitle(self.lang.get('restore_group_title', 'Restore Project'))

        p = self.main_window.theme_manager.current_palette if hasattr(self.main_window, 'theme_manager') else {}
        icon_color = p.get("icon_default", "#e0e0e0")
        self.restore_refresh_btn.setIcon(IconManager.get_icon("dev_patcher.refresh", icon_color))

        self.restore_refresh_btn.setToolTip(self.lang.get('restore_refresh_tooltip', 'Refresh backup list'))
        self.restore_btn.setText(self.lang.get('restore_btn', 'Restore'))
        self.restore_all_btn.setText(self.lang.get('restore_all_btn', 'More...'))

        curr_mode = self.restore_mode_combo.currentData()
        self.restore_mode_combo.blockSignals(True)
        self.restore_mode_combo.clear()
        self.restore_mode_combo.addItem(self.lang.get('restore_mode_changes', 'Only Changes (Standard)'), "changes")
        self.restore_mode_combo.addItem(self.lang.get('restore_mode_full', 'Full Replace (Legacy)'), "full")
        if curr_mode:
            idx = self.restore_mode_combo.findData(curr_mode)
            if idx >= 0: self.restore_mode_combo.setCurrentIndex(idx)
        self.restore_mode_combo.blockSignals(False)


        self.qs_reset_button.setText(self.lang.get('reset_quick_settings_btn'))
        self.qs_apply_button.setText(self.lang.get('apply_quick_settings_btn', 'Apply Settings'))
        self.qs_save_project_button.setText(self.lang.get('save_project_btn', 'Save for Current Project'))
        self.qs_save_project_button.setEnabled(bool(self.main_window.root_path))
        self.qs_save_button.setText(self.lang.get('save_quick_settings_btn', 'Save Global'))

def get_quick_settings():
    return [
        {
            'id': 'dev_patcher_panel',
            'qs_type': 'panel',
            'title_lang_key': 'dev_patcher_quick_settings_title',
            'widget_class': DevPatcherQuickSettingsWidget
        }
    ]