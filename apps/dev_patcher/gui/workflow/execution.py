from PySide6.QtWidgets import QApplication, QMessageBox
from apps.dev_patcher.core.parser import parse_patch_content
from .error_report import show_error_report
from .backup import create_backup

RESTART_CODE = 100

def execute_patch_workflow(manager):
    """Runs the full patch workflow: simulate, backup, execute."""
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

    if is_self_update:
        g_dirs, g_files, _, _, _ = mw.settings_manager.get_ignore_lists()
        ignore_dirs, ignore_files = g_dirs, g_files
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
        skipped_commands = []

    if skipped_commands:
        mw.patcher_log_output.appendPlainText(f"[INFO] Skipping {len(skipped_commands)} problematic commands based on Check Patch results.")

    backup_method = manager.qs_widget.backup_method_combo.currentData()
    if backup_method and backup_method != 'none':
        if not create_backup(manager, target_path, ignore_dirs, ignore_files, is_self_update, commands=final_plan):
            return
        manager.qs_widget._refresh_restore_list()

    manager._exec_total = len(final_plan)
    manager._exec_current_idx = 0
    manager.widget.progress_indicator.start(manager._exec_total, mw.lang.get('patch_run_start_log'))
    manager.widget.run_button.setEnabled(False)

    tc = mw.context.async_thread_manager.thread

    def _exec_task():
        import time
        from systems.fs.real_fs import RealFileSystem
        from apps.dev_patcher.core.patcher import run_patch
        start_total = time.time()
        real_fs = RealFileSystem(target_path)
        real_fs.memory = mw.context.memory
        log_gen = run_patch(final_plan, real_fs, experimental_flags, memory=mw.context.memory)
        failed_commands =[]
        for success, message, command in log_gen:
            if command:
                yield ("cmd_result", success, message, command)
                if not success:
                    failed_commands.append((command, message))
            else:
                yield ("log", success, message, command)
        return failed_commands, time.time() - start_total

    def _on_yield(item):
        type_, success, message, command = item
        if type_ == "cmd_result":
            manager._on_command_result(success, message, command)
        else:
            manager._on_worker_progress(str(message))

    def _on_exec_done(res):
        failed_commands, total_time = res

        if failed_commands:
            manager.widget.progress_indicator.set_error(mw.lang.get('patch_partial_success_warning'))
        else:
            manager.widget.progress_indicator.finish(mw.lang.get('all_commands_success_log'))

        mw.patcher_log_output.appendPlainText(f"Total time: {total_time:.3f}s")
        mw.patcher_log_output.appendPlainText(mw.lang.get('patch_run_end_log'))
        manager.widget.run_button.setEnabled(True)

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

    tc.run_in_background(
        _exec_task,
        use_qt=True,
        yield_callback=_on_yield,
        callback=_on_exec_done,
        error_callback=manager._on_worker_error
    )