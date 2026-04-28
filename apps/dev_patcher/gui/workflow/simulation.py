from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThread, QEventLoop
from apps.dev_patcher.core.parser import parse_patch_content
from apps.dev_patcher.core.patch_worker import PatchWorker
from .error_report import show_error_report

def run_simulation_only(manager):
    """Runs only the simulation step and shows an error report if needed."""
    patch_content, mw = manager._common_setup()
    if not patch_content:
        return

    is_self_update = "@APP-ROOT" in patch_content
    target_path = mw.app_root_path if is_self_update else mw.root_path

    if not is_self_update and not mw.root_path:
        mw.patcher_log_output.appendPlainText(mw.lang.get('project_folder_missing_error'))
        return

    experimental_flags = manager._get_experimental_flags()
    commands = parse_patch_content(patch_content, experimental_flags)

    if not commands:
        mw.patcher_log_output.appendPlainText(mw.lang.get('no_commands_found_log'))
        return

    # Use combined ignore lists
    if is_self_update:
        g_dirs, g_files, _, _, _ = mw.settings_manager.get_ignore_lists()
        ignore_dirs, ignore_files = g_dirs, g_files
    else:
        ignore_dirs, ignore_files = mw.get_combined_ignore_lists()

    mw.patcher_log_output.appendPlainText(mw.lang.get('simulation_start_log'))
    QApplication.processEvents()

    # Reset state
    manager._sim_success = False
    manager._sim_result_data = {}

    # Initialization of the worker
    manager._sim_worker = PatchWorker(commands, target_path, experimental_flags, ignore_dirs, ignore_files, mode='simulate', lang=mw.lang)
    manager._sim_thread = QThread()
    manager._sim_worker.moveToThread(manager._sim_thread)

    # Signals connection
    manager._sim_worker.progress_log.connect(manager._on_worker_progress)
    manager._sim_worker.simulation_finished.connect(manager._on_simulation_finished)
    manager._sim_worker.error.connect(manager._on_worker_error)

    manager._sim_thread.started.connect(manager._sim_worker.run)
    manager._sim_thread.finished.connect(manager._sim_worker.deleteLater)

    # Lock buttons
    manager.widget.check_patch_button.setEnabled(False)
    manager.widget.run_button.setEnabled(False)

    # Start thread and loop
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

    # Unlock buttons
    manager.widget.check_patch_button.setEnabled(True)
    manager.widget.run_button.setEnabled(True)

    mw.patcher_log_output.appendPlainText(mw.lang.get('simulation_end_log'))

    manager.cached_patch_text = patch_content
    manager.cached_plan = manager._sim_result_data.get('plan',[])
    manager.cached_skipped = manager._sim_result_data.get('skipped',[])

    simulation_failures =[]
    for cmd, reason in manager.cached_skipped:
        simulation_failures.append((cmd, reason))

    if simulation_failures:
        from .error_report import show_ai_correction_report
        show_ai_correction_report(manager, simulation_failures)
    else:
        QMessageBox.information(mw, mw.lang.get('simulation_confirm_title'), mw.lang.get('simulation_success_msg_new', "The simulation is complete. No errors found. All commands can be safely executed."))