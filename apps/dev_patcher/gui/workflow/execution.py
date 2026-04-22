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

    if manager.qs_widget.corrector_checkbox.isChecked():
        patch_was_modified, new_patch_content = run_corrector(manager, patch_content)
        if patch_was_modified is None:
            return
        if patch_was_modified:
            patch_content = new_patch_content

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

    final_plan, skipped_commands =[],[]

    if manager.qs_widget.simulate_checkbox.isChecked():
        mw.patcher_log_output.appendPlainText(mw.lang.get('simulation_start_log'))
        QApplication.processEvents()

        # Reset State
        manager._sim_success = False
        manager._sim_result_data = {}

        # Init Simulation Worker
        manager._sim_worker = PatchWorker(commands, target_path, experimental_flags, ignore_dirs, ignore_files, mode='simulate', lang=mw.lang)
        manager._sim_thread = QThread()
        manager._sim_worker.moveToThread(manager._sim_thread)

        # Connections
        manager._sim_worker.progress_log.connect(manager._on_worker_progress)
        manager._sim_worker.simulation_finished.connect(manager._on_simulation_finished)
        manager._sim_worker.error.connect(manager._on_worker_error)

        manager._sim_thread.started.connect(manager._sim_worker.run)
        manager._sim_thread.finished.connect(manager._sim_worker.deleteLater)

        manager.widget.run_button.setEnabled(False)

        manager._active_loop = QEventLoop()
        manager._sim_thread.start()
        manager._active_loop.exec()

        # Cleanup
        manager._sim_thread.quit()
        manager._sim_thread.wait()
        manager._sim_worker = None
        if manager._sim_thread:
            manager._sim_thread.deleteLater()
        manager._sim_thread = None
        manager._active_loop = None

        manager.widget.run_button.setEnabled(True)

        mw.patcher_log_output.appendPlainText(mw.lang.get('simulation_end_log'))

        final_plan = manager._sim_result_data.get('plan', [])
        skipped_commands = manager._sim_result_data.get('skipped',[])

        has_skips = bool(skipped_commands)
        msg_box_text = mw.lang.get('simulation_error_msg') if has_skips else mw.lang.get('simulation_success_msg')

        reply = QMessageBox.question(mw, mw.lang.get('simulation_confirm_title'), msg_box_text,
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.No:
            mw.patcher_log_output.appendPlainText(mw.lang.get('simulation_cancelled_log'))
            return

    else:
        final_plan = commands

    if skipped_commands:
        simulation_failures =[]
        for cmd, reason in skipped_commands:
            simulation_failures.append((cmd, reason))
        show_error_report(manager, simulation_failures)

    # Start Code Check phase if enabled
    if manager.qs_widget.code_check_checkbox.isChecked():
        mw.patcher_log_output.appendPlainText(mw.lang.get('code_check_running_log'))
        QApplication.processEvents()

        vfs = simulate_patch_and_get_vfs(commands, target_path, experimental_flags, ignore_dirs)
        checker = CodeChecker(vfs, target_path)

        for log_line in checker.run():
            mw.patcher_log_output.appendPlainText(log_line)
            QApplication.processEvents()

        if checker.errors:
            formatted_errors =[(("CodeCheck", [fp], ""), err) for fp, err in checker.errors]
            show_error_report(manager, formatted_errors)

            msg_box_text = mw.lang.get('code_check_error_msg')
            reply = QMessageBox.warning(mw, mw.lang.get('simulation_confirm_title'), msg_box_text,
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.No:
                mw.patcher_log_output.appendPlainText(mw.lang.get('simulation_cancelled_log'))
                return
        else:
            mw.patcher_log_output.appendPlainText(mw.lang.get('code_check_no_errors_log'))

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