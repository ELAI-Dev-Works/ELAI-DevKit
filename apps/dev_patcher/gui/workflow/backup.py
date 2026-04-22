from PySide6.QtWidgets import QMessageBox
from apps.dev_patcher.core.backup import create_backup as core_create_backup
from apps.dev_patcher.core.backup import create_git_backup

from apps.dev_patcher.core.backup import BackupBuilder

def build_backup_actions(commands, target_path, extension_manager):
    builder = BackupBuilder(target_path)
    if not commands: return[]

    import importlib
    from apps.dev_patcher.core.custom_loader import CustomCommandLoader

    loader = CustomCommandLoader(target_path)

    for cmd in commands:
        name, args, content = cmd

        if name.upper() == 'TEST':
            continue

        try:
            tool_instance = None
            try:
                module_name = f"apps.dev_patcher.core.commands.{name.lower()}"
                tool_module = importlib.import_module(module_name)
                tool_instance = tool_module.Command()
            except ImportError:
                tool_module = loader.find_command(name)
                if tool_module and hasattr(tool_module, 'Command'):
                    tool_instance = tool_module.Command()

            if tool_instance and hasattr(tool_instance, 'build_backup'):
                tool_instance.build_backup(args, content, target_path, builder)
            else:
                for arg in args:
                    if '@ROOT/' in arg or '@ROOT\\' in arg:
                        path = arg.replace('@ROOT/', '').replace('@ROOT\\', '').strip('\'"')
                        if path not in ('to', 'as'):
                            builder.use('replace', path)
        except Exception as e:
            print(f"Failed to build backup actions for {name}: {e}")

    return builder.actions

def create_backup(manager, target_path, ignore_dirs, ignore_files, is_self_update, commands=None):
    if commands and all(cmd[0].upper() == 'TEST' for cmd in commands):
        return True

    backup_actions = build_backup_actions(commands, target_path, manager.main_window.extension_manager) if commands else[]
    mw = manager.main_window
    backup_settings = mw.settings_manager.get_setting(['apps', 'dev_patcher', 'quick', 'Backup'], {})
    method = backup_settings.get('method', 'zip')
    commit_msg = backup_settings.get('commit_message', 'Auto-backup before patching')

    if method == 'none' or method is False:
        return True

    if method is True:
        method = 'zip'

    target_name = mw.lang.get('app_target_name' if is_self_update else 'project_target_name')

    if method in ['zip', 'all']:
        mw.patcher_log_output.appendPlainText(mw.lang.get('backup_creation_log').format(target_name))
        success, msg = core_create_backup(target_path, ignore_dirs=ignore_dirs, ignore_files=ignore_files, backup_actions=backup_actions)
        if not success:
            QMessageBox.critical(mw, mw.lang.get('patch_load_error_title'), mw.lang.get('backup_failed_error_msg').format(target_name, msg))
            return False
        mw.patcher_log_output.appendPlainText(mw.lang.get('backup_success_log').format(msg))

    if method in ['git', 'all']:
        mw.patcher_log_output.appendPlainText(mw.lang.get('backup_git_creation_log').format(target_name))
        success, msg = create_git_backup(target_path, commit_msg, ignore_dirs, ignore_files, backup_actions=backup_actions)
        if not success:
            QMessageBox.critical(mw, mw.lang.get('patch_load_error_title'), mw.lang.get('backup_git_failed_error_msg').format(target_name, msg))
            return False
        mw.patcher_log_output.appendPlainText(mw.lang.get('backup_git_success_log').format(msg))

    return True