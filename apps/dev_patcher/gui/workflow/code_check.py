from PySide6.QtWidgets import QApplication
from apps.dev_patcher.core.parser import parse_patch_content
from apps.dev_patcher.core.patch_checking import simulate_patch_and_get_vfs
from apps.dev_patcher.core.code_check.checker import CodeChecker
from .error_report import show_error_report

def run_code_check(manager):
    """Runs the code syntax check workflow manually."""
    patch_content, mw = manager._common_setup()
    if not patch_content: return

    is_self_update = "@APP-ROOT" in patch_content
    target_path = mw.app_root_path if is_self_update else mw.root_path

    if not is_self_update and not mw.root_path:
        mw.patcher_log_output.appendPlainText(mw.lang.get('project_folder_missing_error'))
        return

    mw.patcher_log_output.appendPlainText(mw.lang.get('code_check_start_log'))
    QApplication.processEvents()

    experimental_flags = manager._get_experimental_flags()
    if is_self_update:
        g_dirs, g_files, _, _, _ = mw.settings_manager.get_ignore_lists()
        ignore_dirs, ignore_files = g_dirs, g_files
    else:
        ignore_dirs, ignore_files = mw.get_combined_ignore_lists()

    commands = parse_patch_content(patch_content, experimental_flags)
    if not commands:
        mw.patcher_log_output.appendPlainText(mw.lang.get('no_commands_found_log'))
        return

    mw.patcher_log_output.appendPlainText(mw.lang.get('code_check_running_log'))
    QApplication.processEvents()

    vfs = simulate_patch_and_get_vfs(commands, target_path, experimental_flags, ignore_dirs)
    checker = CodeChecker(vfs, target_path)

    for log_line in checker.run():
        mw.patcher_log_output.appendPlainText(log_line)
        QApplication.processEvents()

    if checker.errors:
        mw.patcher_log_output.appendPlainText(mw.lang.get('code_check_errors_found_log'))
        formatted_errors = [(("CodeCheck", [fp], ""), err) for fp, err in checker.errors]
        show_error_report(manager, formatted_errors)
    else:
        mw.patcher_log_output.appendPlainText(mw.lang.get('code_check_no_errors_log'))

    mw.patcher_log_output.appendPlainText(mw.lang.get('code_check_finished_log'))