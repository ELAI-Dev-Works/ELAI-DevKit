from PySide6.QtWidgets import QApplication, QMessageBox
from apps.dev_patcher.core.parser import parse_patch_content
from apps.dev_patcher.core.patch_checking import simulate_patch_and_get_vfs
from apps.dev_patcher.core.test_runner import TestRunner
from apps.dev_patcher.gui.windows.test_report import TestReportDialog

def run_test_launch(manager):
    """Runs the test launch workflow."""
    patch_content, mw = manager._common_setup()
    if not patch_content:
        return


    if 'project_launcher' not in mw.tabs or not mw.extension_manager.extensions.get('project_launcher', {}).get('enabled'):
        mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_dependency_error'))
        QMessageBox.critical(mw, mw.lang.get('patch_load_error_title'), mw.lang.get('test_run_dependency_error'))
        return

    if not mw.root_path:
        mw.patcher_log_output.appendPlainText(mw.lang.get('project_folder_missing_error'))
        return

    project_launcher_widget = mw.tabs.get('project_launcher')
    launch_file = project_launcher_widget.launch_file_combo.currentText() if project_launcher_widget else None

    if not launch_file:
        QMessageBox.warning(mw, mw.lang.get('patch_load_error_title'), mw.lang.get('test_run_invalid_file_error'))
        return

    mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_start_log'))
    QApplication.processEvents()

    experimental_flags = manager._get_experimental_flags()
    commands = parse_patch_content(patch_content, experimental_flags)
    if not commands:
        mw.patcher_log_output.appendPlainText(mw.lang.get('no_commands_found_log'))
        return

    mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_simulating_log'))
    QApplication.processEvents()

    # Test Run uses synchronous simulation (without threads) as TestRunner awaits VFS object
    # Use combined ignore lists from MainWindow
    ignore_dirs, _ = mw.get_combined_ignore_lists()
    vfs = simulate_patch_and_get_vfs(commands, mw.root_path, experimental_flags, ignore_dirs)

    mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_launching_log'))
    QApplication.processEvents()

    runner = TestRunner(vfs, mw.root_path, launch_file)
    log_generator = runner.run()

    log_lines =[]
    for line in log_generator:
        log_lines.append(line)
        mw.patcher_log_output.appendPlainText(line)
        QApplication.processEvents()

    report_dialog = TestReportDialog("\n".join(log_lines), mw)
    report_dialog.exec()

    mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_finished_log'))