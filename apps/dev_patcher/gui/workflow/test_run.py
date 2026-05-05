import os
from PySide6.QtWidgets import QApplication, QMessageBox
from apps.dev_patcher.core.parser import parse_patch_content
from apps.dev_patcher.core.patch_checking import simulate_patch_and_get_vfs
from apps.dev_patcher.core.test_run.runner import TestRunner
from apps.dev_patcher.core.test_run.architectures import get_architecture
from apps.dev_patcher.gui.windows.test_run_dialog import TestFileSelectDialog
from apps.dev_patcher.gui.windows.test_console import TestConsoleWindow
from apps.dev_patcher.gui.windows.test_report import TestReportDialog

def run_test_launch(manager):
    """Runs the test launch workflow with sandbox and interactive console."""
    patch_content, mw = manager._common_setup()
    if not patch_content:
        return

    if not mw.root_path:
        mw.patcher_log_output.appendPlainText(mw.lang.get('project_folder_missing_error'))
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

    ignore_dirs, _ = mw.get_combined_ignore_lists()
    vfs = simulate_patch_and_get_vfs(commands, mw.root_path, experimental_flags, ignore_dirs, memory=mw.context.memory)

    needs_env = False
    env_indicators =[
        '@ROOT/requirements.txt', '@ROOT/requirements.in', '@ROOT/package.json',
        '@ROOT/setup_run(uv).bat', '@ROOT/run(pip).bat', '@ROOT/run(nodejs).bat',
        '@ROOT/setup_run(uv).sh', '@ROOT/run(pip).sh', '@ROOT/run(nodejs).sh'
    ]
    for indicator in env_indicators:
        if vfs.exists(indicator):
            needs_env = True
            break

    if not needs_env:
        for cmd_name, args, content in commands:
            if cmd_name.upper() == 'PROJECT' and '-setup' in args:
                needs_env = True
                break
            if '.venv' in content or 'node_modules' in content or 'npm install' in content or 'pip install' in content or 'uv venv' in content:
                needs_env = True
                break

    if needs_env:
        has_env = os.path.exists(os.path.join(mw.root_path, '.venv')) or os.path.exists(os.path.join(mw.root_path, 'node_modules'))
        if not has_env:
            error_msg = mw.lang.get('test_run_env_required_error')
            mw.patcher_log_output.appendPlainText(f"[Error] {error_msg}")
            QMessageBox.warning(mw, mw.lang.get('test_run_aborted_title', "Test Run Aborted"), error_msg)
            return
    
    # 1. Open dialog for test file selection
    dialog = TestFileSelectDialog(vfs, mw)
    if not dialog.exec() or not dialog.selected_file:
        mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_finished_log'))
        return
    launch_file = dialog.selected_file
    
    mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_launching_log'))
    QApplication.processEvents()
    
    # 2. Setup Runner and Architecture asynchronously
    runner = TestRunner(vfs, mw.root_path, mw.context)

    def _on_prepared(temp_dir):
        try:
            arch = get_architecture(temp_dir, mw.root_path, launch_file)
            is_trusted = getattr(mw.context.security_manager, 'is_trusted_session', False)
            launch_cmd = arch.get_launch_command(is_trusted=is_trusted)

            if launch_cmd.startswith("HTML:"):
                html_file = launch_cmd[5:]
                from systems.os.platform import open_file_externally
                open_file_externally(html_file)

                mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_html_info_log', "[INFO] HTML file opened in default browser."))
                QMessageBox.information(mw, mw.lang.get('test_run_html_dialog_title', "HTML Test"), mw.lang.get('test_run_html_dialog_msg', "HTML file opened in your browser. Close this dialog when you are done to clean up the test environment."))
                final_log = mw.lang.get('test_run_html_final_log', "[INFO] HTML Test run via external browser.")
            else:
                console_win = TestConsoleWindow(temp_dir, launch_cmd, mw, cwd=temp_dir)
                console_win.exec()
                final_log = console_win.final_log

            report_dialog = TestReportDialog(final_log, mw)
            report_dialog.exec()

        except Exception as e:
            import traceback
            mw.patcher_log_output.appendPlainText("\n" + mw.lang.get('test_run_critical_error_log', "[ERROR] Critical error during test run: {}").format(e))
            mw.patcher_log_output.appendPlainText(traceback.format_exc())
        finally:
            runner.cleanup()
            mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_finished_log'))

    def _on_prepare_error(error):
        from systems.error_handler.logger import log_to_file
        from PySide6.QtWidgets import QMessageBox
        error_msg = mw.lang.get('test_run_prep_error_log', "Failed to prepare test environment: {}").format(error)
        mw.patcher_log_output.appendPlainText(error_msg)
        log_to_file(f"TestRun preparation error: {error}", is_exception=True)
        QMessageBox.critical(mw, mw.lang.get('test_run_error_title', "Test Run Error"), error_msg)
        try:
            runner.cleanup()
        except Exception:
            pass
        mw.patcher_log_output.appendPlainText(mw.lang.get('test_run_finished_log'))

    tc = mw.context.async_thread_manager.thread
    manager._test_run_worker = tc.run_in_background(runner.prepare, callback=_on_prepared, error_callback=_on_prepare_error, use_qt=True)