from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject, Slot

from .workflow.corrector import run_correction_only
from .workflow.simulation import run_simulation_only
from .workflow.code_check import run_code_check
from .workflow.test_run import run_test_launch
from .workflow.execution import execute_patch_workflow

class PatchWorkflowManager(QObject):
    def __init__(self, dev_patcher_widget):
        super().__init__() # Initialize QObject for signal/slot support
        self.main_window = dev_patcher_widget.main_window
        self.widget = dev_patcher_widget
        self.qs_widget = None

        # Worker state management
        self._sim_worker = None
        self._sim_thread = None
        self._exec_worker = None
        self._exec_thread = None

        # Event loop state variables
        self._active_loop = None
        self._sim_success = False
        self._sim_result_data = {}
        self._exec_failed_commands =[]

        # Execution progress tracking
        self._exec_current_idx = 0
        self._exec_total = 0

        # Cache for execution plan
        self.cached_patch_text = ""
        self.cached_plan = None
        self.cached_skipped = None


    def set_quick_settings_widget(self, qs_widget):
        self.qs_widget = qs_widget

    def _common_setup(self):
        """Performs common setup for all workflow actions."""
        mw = self.main_window
        log_output = mw.patcher_log_output
        log_output.clear()
        log_output.appendPlainText(mw.lang.get('log_cleared'))

        patch_content = self.widget.patch_input.toPlainText()
        if not patch_content.strip():
            log_output.appendPlainText(mw.lang.get('patch_empty_error'))
            return None, None

        return patch_content, mw

    # --- Slots for Thread Safety ---
    @Slot(str)
    def _on_worker_progress(self, message):
        """Thread-safe slot to update log."""
        self.main_window.patcher_log_output.appendPlainText(message)

    @Slot(str)
    def _on_worker_error(self, message):
        """Thread-safe slot for critical errors."""
        self.main_window.patcher_log_output.appendPlainText(f"\n[CRITICAL ERROR] {message}")
        if self._active_loop:
            self._active_loop.quit()

    @Slot(bool, dict)
    def _on_simulation_finished(self, success, result):
        """Thread-safe slot when simulation ends."""
        self._sim_success = success
        self._sim_result_data = result
        if self._active_loop:
            self._active_loop.quit()

    @Slot(list, float)
    def _on_execution_finished(self, failed_commands, total_time):
        """Thread-safe slot when real execution ends."""
        self._exec_failed_commands = failed_commands

        # Update UI state
        if failed_commands:
            self.widget.progress_indicator.set_error(self.main_window.lang.get('patch_partial_success_warning'))
        else:
            self.widget.progress_indicator.finish(self.main_window.lang.get('all_commands_success_log'))

        self.main_window.patcher_log_output.appendPlainText(f"Total time: {total_time:.3f}s")
        self.main_window.patcher_log_output.appendPlainText(self.main_window.lang.get('patch_run_end_log'))
        self.widget.run_button.setEnabled(True)
        if self._active_loop:
            self._active_loop.quit()

    @Slot(bool, str, tuple)
    def _on_command_result(self, success, message, command):
        """Thread-safe slot for individual command results during execution."""
        self._exec_current_idx += 1

        # Update progress bar
        self.widget.progress_indicator.update_progress(self._exec_current_idx)

        cmd_name = command[0]
        cmd_args = " ".join(command[1])
        cmd_header = f"<{cmd_name} {cmd_args}>"

        log_prefix = self.main_window.lang.get('patch_command_log').format(self._exec_current_idx, self._exec_total)

        if not success:
            self.main_window.patcher_log_output.appendPlainText(f"{log_prefix} {cmd_header} -> " + self.main_window.lang.get('patch_command_error_log').format(message))
        else:
            full_message = message if message else self.main_window.lang.get('command_executed_default_msg')
            self.main_window.patcher_log_output.appendPlainText(f"{log_prefix} {cmd_header} -> " + self.main_window.lang.get('patch_command_success_log').format(full_message))

    # --- Public Workflow Methods ---

    def run_correction_only(self):
        run_correction_only(self)

    def run_simulation_only(self):
        run_simulation_only(self)

    def run_code_check(self):
        run_code_check(self)

    def run_test_launch(self):
        run_test_launch(self)

    def execute_patch_workflow(self):
        execute_patch_workflow(self)

    @Slot(int)
    def show_diff_for_line(self, line_number):
        mw = self.main_window
        target_path = mw.root_path

        patch_content = self.widget.patch_input.toPlainText()
        lines = patch_content.splitlines()

        block_lines =[]
        for i in range(line_number, len(lines)):
            line = lines[i]
            block_lines.append(line)
            if line.strip() == "---end---" or line.strip() == "---end---{!END}":
                break

        command_text = "\n".join(block_lines)

        from apps.dev_patcher.core.parser import parse_patch_content
        experimental_flags = self._get_experimental_flags()
        commands = parse_patch_content(command_text, experimental_flags)

        if not commands:
            QMessageBox.warning(self.widget, "Error", "Could not parse the EDIT command.")
            return

        command = commands[0]
        cmd_name, args, content = command

        if cmd_name.upper() != "EDIT":
            QMessageBox.warning(self.widget, "Error", "Selected command is not an EDIT command.")
            return

        if not target_path:
            QMessageBox.warning(self.widget, "Error", mw.lang.get('project_folder_missing_error'))
            return

        from apps.dev_patcher.core.patcher import _normalize_edit_args
        norm_args = _normalize_edit_args(args)
        if len(norm_args) < 2:
            QMessageBox.warning(self.widget, "Error", "EDIT command is missing arguments.")
            return

        file_path = norm_args[1].replace('@ROOT/', '').replace('@ROOT\\', '').replace('@ROOT', '').strip("'\"")

        import os
        full_path = os.path.join(target_path, file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    original_content = f.read()
            except Exception as e:
                QMessageBox.warning(self.widget, "Error", f"Failed to read file: {e}")
                return
        else:
            QMessageBox.warning(self.widget, "Error", f"File not found: {full_path}")
            return

        from apps.dev_patcher.core.commands.edit.tool import EditTool
        from apps.dev_patcher.core.patcher_tools.extra_tool import Tool as ExtraEditTool
        from apps.dev_patcher.core.patcher_tools.experimental.precise_patching import Tool as ExperimentalEditTool

        use_lineno = experimental_flags.get("lineno")
        use_extra = experimental_flags.get("fuzzy") or experimental_flags.get("scope")

        if use_lineno:
            edit_tool = ExperimentalEditTool()
            plan = edit_tool.plan_edit(norm_args, content, original_content, experimental_flags)
        elif use_extra:
            edit_tool = ExtraEditTool()
            plan = edit_tool.plan_edit(norm_args, content, original_content, experimental_flags)
        else:
            edit_tool = EditTool()
            plan = edit_tool.plan_edit(norm_args, content, original_content)

        if not plan.get("success"):
            QMessageBox.warning(self.widget, "Diff Error", f"Could not apply patch for preview:\n{plan.get('message')}")
            return

        lines_orig = original_content.splitlines()
        start, end = plan['start_line'], plan['end_line']
        lines_orig[start:end] = plan['new_lines']
        new_content = "\n".join(lines_orig)

        from apps.dev_patcher.gui.windows.diff_viewer import DiffViewerDialog
        dialog = DiffViewerDialog(self.widget, file_path, original_content, new_content)
        dialog.exec()


    def _confirm_self_update(self):
        mw = self.main_window
        mw.patcher_log_output.appendPlainText(mw.lang.get('self_update_mode_log'))
        reply = QMessageBox.warning(mw, mw.lang.get('self_update_warning_title'), mw.lang.get('self_update_warning_msg'),
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            mw.patcher_log_output.appendPlainText(mw.lang.get('self_update_cancelled_log'))
            return False
        return True

    def _get_experimental_flags(self):
        qs = self.qs_widget
        return {
            "enabled": True,
            "fuzzy": qs.fuzzy_checkbox.isChecked(),
            "scope": qs.scope_checkbox.isChecked(),
            "lineno": qs.lineno_checkbox.isChecked(),
            "threshold": qs.similarity_spinbox.value() / 100.0,
        }