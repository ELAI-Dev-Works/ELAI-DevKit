from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThread, QEventLoop
from apps.dev_patcher.core.parser import parse_patch_content
from apps.dev_patcher.core.patch_worker import PatchWorker
from apps.dev_patcher.core.patch_checking import simulate_patch_and_get_vfs
from apps.dev_patcher.core.code_check.checker import CodeChecker
from .error_report import show_error_report
from .corrector import run_corrector
from .backup import create_backup

RESTART_CODE = 100

def execute_patch_workflow(manager):
    """Runs the full patch workflow: correct, simulate, execute."""
    patch_content, mw = manager._common_setup()
    if not patch_content:
        return

    is_self_update = "@APP-ROOT" in patch_content
    target_path = mw.app_root_path if is_self_update else mw.root_path

    if is_self_update:
        if not manager._confirm_self_update():
            return
    elif not mw.root_path:
        mw.patcher_log_output.appendPlainText(mw.lang.get('project_folder_missing_error'))
        return

    experimental_flags = manager._get_experimental_flags()
    commands = parse_patch_content(patch_content, experimental_flags)

    # Use combined ignore lists
    if is_self_update:
        ignore_dirs, ignore_files, _ = mw.settings_manager.get_ignore_lists()
    else:
        ignore_dirs, ignore_files = mw.get_combined_ignore_lists()

    if not commands:
        mw.patcher_log_output.appendPlainText(mw.lang.get('no_commands_found_log'))
        return

    if patch_content == manager.cached_patch_text and manager.cached_plan is not None:
        final_plan = manager.cached_plan
        skipped_commands = manager.cached_skipped
    else:
        final_plan = commands
        skipped_commands =[]

    if skipped_commands:
        mw.patcher_log_output.appendPlainText(f"[INFO] Skipping {len(skipped_commands)} problematic commands based on Check Patch results.")

    backup_method = manager.qs_widget.backup_method_combo.currentData()
    if backup_method and backup_method != 'none':
        if not create_backup(manager, target_path, ignore_dirs, ignore_files, is_self_update, commands=final_plan):
            return
        manager.qs_widget._refresh_restore_list()

    # Start Progress Bar
    total_commands = len(final_plan)
    manager.widget.progress_indicator.start(total_commands, mw.lang.get('patch_run_start_log'))

    # Run Real Execution
    _run_real_patch_thread(manager, final_plan, target_path, experimental_flags)

    # After _run_real_patch_thread returns (it blocks via loop), check results
    failed_commands = manager._exec_failed_commands

    if failed_commands:
        mw.patcher_log_output.appendPlainText("\n--- ERRORS DURING REAL EXECUTION ---")
        show_error_report(manager, failed_commands)
    elif not skipped_commands:
        mw.patcher_log_output.appendPlainText(mw.lang.get('all_commands_success_log'))
    else:
        mw.patcher_log_output.appendPlainText("\n" + mw.lang.get('patch_partial_success_warning'))

    if is_self_update and not failed_commands:
        QMessageBox.information(mw, mw.lang.get('update_complete_title'), mw.lang.get('update_complete_msg'))
        QApplication.exit(RESTART_CODE)

def _run_real_patch_thread(manager, commands, target_path, experimental_flags):
    mw = manager.main_window
    mw.patcher_log_output.appendPlainText(mw.lang.get('patch_run_start_log'))

    # Reset counters
    manager._exec_current_idx = 0
    manager._exec_total = len(commands)
    manager._exec_failed_commands =[]

    # Init Execution Worker
    manager._exec_worker = PatchWorker(commands, target_path, experimental_flags,
                         ignore_dirs=[], ignore_files=[],
                         mode='execute', lang=mw.lang)

    manager._exec_thread = QThread()
    manager._exec_worker.moveToThread(manager._exec_thread)

    # Connections
    manager._exec_worker.command_result.connect(manager._on_command_result)
    manager._exec_worker.execution_finished.connect(manager._on_execution_finished)
    manager._exec_worker.error.connect(manager._on_worker_error)

    manager._exec_thread.started.connect(manager._exec_worker.run)
    manager._exec_thread.finished.connect(manager._exec_worker.deleteLater)

    manager.widget.run_button.setEnabled(False)

    manager._active_loop = QEventLoop()
    manager._exec_thread.start()
    manager._active_loop.exec()

    # Cleanup
    manager._exec_thread.quit()
    manager._exec_thread.wait()

    manager._exec_worker = None
    if manager._exec_thread:
        manager._exec_thread.deleteLater()
    manager._exec_thread = None
    manager._active_loop = None