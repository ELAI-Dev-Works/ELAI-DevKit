from PySide6.QtWidgets import QApplication, QMessageBox
from apps.dev_patcher.core.parser import parse_patch_content
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

    if is_self_update:
        g_dirs, g_files, _, _, _ = mw.settings_manager.get_ignore_lists()
        ignore_dirs, ignore_files = g_dirs, g_files
    else:
        ignore_dirs, ignore_files = mw.get_combined_ignore_lists()

    mw.patcher_log_output.appendPlainText(mw.lang.get('simulation_start_log'))
    QApplication.processEvents()

    manager.widget.check_patch_button.setEnabled(False)
    manager.widget.run_button.setEnabled(False)

    tc = mw.context.async_thread_manager.thread

    def _sim_task():
        from apps.dev_patcher.core.patch_checking import plan_dynamic_patch
        sim_gen = plan_dynamic_patch(commands, target_path, experimental_flags, ignore_dirs, mw.lang, memory=mw.context.memory)
        final_result = {}
        success = True
        for item in sim_gen:
            if isinstance(item, tuple) and item[0] == 'finished':
                final_result = item[1]
                break
            elif isinstance(item, tuple) and item[0] == 'analysis_failure':
                fail_msg = item[1][1] if len(item[1]) > 1 else str(item[1])
                yield f"Analysis Failure: {fail_msg}"
                success = False
            else:
                yield str(item)
        if final_result.get('skipped'):
            success = False
        return success, final_result

    def _on_sim_done(res):
        success, final_result = res
        manager.widget.check_patch_button.setEnabled(True)
        manager.widget.run_button.setEnabled(True)
        mw.patcher_log_output.appendPlainText(mw.lang.get('simulation_end_log'))

        manager.cached_patch_text = patch_content
        manager.cached_plan = final_result.get('plan', [])
        manager.cached_skipped = final_result.get('skipped',[])

        simulation_failures =[]
        for cmd, reason in manager.cached_skipped:
            simulation_failures.append((cmd, reason))

        if simulation_failures:
            from .error_report import show_ai_correction_report
            show_ai_correction_report(manager, simulation_failures)
        else:
            QMessageBox.information(mw, mw.lang.get('simulation_confirm_title'), mw.lang.get('simulation_success_msg_new', "The simulation is complete. No errors found. All commands can be safely executed."))

    tc.run_in_background(
        _sim_task,
        use_qt=True,
        yield_callback=manager._on_worker_progress,
        callback=_on_sim_done,
        error_callback=manager._on_worker_error
    )