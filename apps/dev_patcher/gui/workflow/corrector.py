from apps.dev_patcher.core.corrector import PatchCorrector
from apps.dev_patcher.gui.windows.corrector import CorrectorDialog

def run_correction_only(manager):
    """Runs only the syntax correction step."""
    patch_content, mw = manager._common_setup()
    if not patch_content:
        return

    patch_was_modified, _ = run_corrector(manager, patch_content)
    if patch_was_modified is None:
        return

    if patch_was_modified:
        mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_done_log'))
    else:
        mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_no_issues_log'))

def run_corrector(manager, patch_content):
    mw = manager.main_window
    experimental_flags = manager._get_experimental_flags()
    corrector = PatchCorrector(patch_content, experimental_flags, mw.lang)
    issues = corrector.analyze()

    if not issues:
        return False, patch_content

    mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_issues_found_log'))
    corrector_dialog = CorrectorDialog(issues, patch_content, mw, manager.qs_widget)

    if corrector_dialog.exec():
        corrected_patch, was_modified = corrector_dialog.get_corrected_patch()
        if was_modified:
            manager.widget.patch_input.setPlainText(corrected_patch)
            mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_patch_updated_log'))
        return True, corrected_patch
    else:
        mw.patcher_log_output.appendPlainText(mw.lang.get('corrector_cancelled_log'))
        return None, None