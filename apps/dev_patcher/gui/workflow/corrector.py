def run_correction_only(manager):
    """Runs only the syntax correction step via background task."""
    patch_content, mw = manager._common_setup()
    if not patch_content:
        return

    tc = mw.context.async_thread_manager.thread
    manager.widget.correct_patch_button.setEnabled(False)

    def _analyze_task():
        from apps.dev_patcher.core.corrector import PatchCorrector
        experimental_flags = manager._get_experimental_flags()
        corrector = PatchCorrector(patch_content, experimental_flags, mw.lang)
        return corrector.analyze()

    def _on_analyzed(issues):
        manager.widget.correct_patch_button.setEnabled(True)
        if not issues:
            mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_no_issues_log'))
            return

        mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_issues_found_log'))
        from apps.dev_patcher.gui.windows.corrector import CorrectorDialog
        corrector_dialog = CorrectorDialog(issues, patch_content, mw, manager.qs_widget)
        if corrector_dialog.exec():
            corrected_patch, was_modified = corrector_dialog.get_corrected_patch()
            if was_modified:
                manager.widget.patch_input.setPlainText(corrected_patch)
                mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_patch_updated_log'))
            mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_done_log'))
        else:
            mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_cancelled_log'))

    tc.run_in_background(_analyze_task, callback=_on_analyzed, use_qt=True)