from PySide6.QtWidgets import (
    QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QFileDialog, QLabel,
    QFrame, QCheckBox, QMessageBox, QGroupBox, QFormLayout,
    QSpacerItem, QSizePolicy, QSpinBox
)
from PySide6.QtCore import Qt
import os
from .patch_workflow import PatchWorkflowManager
from ..app import DevPatcherApp
from .windows.examples import ExamplesDialog
from systems.gui.widgets.quick_settings_panel import QuickSettingsPanel

from plugins.code_editor.editor import CodeEditor
from apps.dev_patcher.gui.highlighting.dpcl import DPCLHighlighter

from systems.gui.widgets.task_progress import TaskProgressIndicator

class DevPatcherInterface(QWidget):
    def __init__(self, context, app_instance):
        super().__init__()

        # Handle context being either AppContext or MainWindow (QWidget)
        if isinstance(context, QWidget):
            self.main_window = context
            self.context = getattr(context, 'context', None)
        else:
            self.context = context
            self.main_window = getattr(context, 'main_window', None)

        self.lang = self.context.lang if self.context else self.main_window.lang
        self.app = app_instance
        self.app.set_widget(self)
        self.patch_workflow_manager = PatchWorkflowManager(self)
        self.app.patch_workflow_manager = self.patch_workflow_manager

        self.init_ui()

        # Pass the quick settings widget to the manager now that it exists
        self.patch_workflow_manager.set_quick_settings_widget(
            self.quick_settings_panel.accordions['dev_patcher'][1]
        )
        
        self.retranslate_ui()

    def init_ui(self):
        """Initializes the UI for the Dev Patcher tab."""
        patcher_layout = QVBoxLayout(self)
        patcher_layout.setContentsMargins(0,0,0,0)

        self.patch_input = CodeEditor()
        self.highlighter = DPCLHighlighter(self.patch_input.document())
        self.patch_input.diff_requested.connect(self.patch_workflow_manager.show_diff_for_line)
        patcher_layout.addWidget(self.patch_input, stretch=2)
    
        # --- Quick Settings Panel (now integrated) ---
        self.quick_settings_panel = QuickSettingsPanel(self.main_window, extension_name_filter='dev_patcher')
        patcher_layout.addWidget(self.quick_settings_panel)
    
        self.progress_indicator = TaskProgressIndicator()
        patcher_layout.addWidget(self.progress_indicator)
        
        action_panel = self._create_action_panel()
        patcher_layout.addWidget(action_panel)
        
        self.patcher_log_output = self.main_window.patcher_log_output
        patcher_layout.addWidget(self.patcher_log_output, stretch=1)


    def _create_action_panel(self):
        """Creates the panel with main action buttons like 'Apply Patch'."""
        action_panel = QFrame()
        action_layout = QHBoxLayout(action_panel)
        self.load_patch_button = QPushButton()
        self.load_patch_button.clicked.connect(self.app.load_patch_from_file)
        action_layout.addWidget(self.load_patch_button)
        
        self.examples_button = QPushButton()
        self.examples_button.clicked.connect(self._open_examples_dialog)
        action_layout.addWidget(self.examples_button)
        
        action_layout.addStretch()

        self.correct_patch_button = QPushButton()
        self.correct_patch_button.clicked.connect(self.patch_workflow_manager.run_correction_only)
        action_layout.addWidget(self.correct_patch_button)

        self.check_patch_button = QPushButton()
        self.check_patch_button.clicked.connect(self.patch_workflow_manager.run_simulation_only)
        action_layout.addWidget(self.check_patch_button)

        self.check_code_button = QPushButton()
        self.check_code_button.clicked.connect(self.patch_workflow_manager.run_code_check)
        action_layout.addWidget(self.check_code_button)

        self.test_run_button = QPushButton()
        self.test_run_button.clicked.connect(self.patch_workflow_manager.run_test_launch)
        action_layout.addWidget(self.test_run_button)

        self.run_button = QPushButton()
        self.run_button.clicked.connect(self.patch_workflow_manager.execute_patch_workflow)
        action_layout.addWidget(self.run_button)

        return action_panel



    def retranslate_ui(self):
        """Applies all translations to the UI elements."""
        if hasattr(self.main_window, 'theme_manager'):
            p = self.main_window.theme_manager.current_palette
            if hasattr(self.patch_input, 'update_theme_colors'):
                self.patch_input.update_theme_colors(p)
            if hasattr(self.quick_settings_panel, 'update_icons'):
                self.quick_settings_panel.update_icons()

        self.patch_input.setPlaceholderText(self.lang.get('patch_input_placeholder'))
        self.examples_button.setText(self.lang.get('examples_btn')).addGUITooltip(self.lang.get('examples_tooltip'))
        self.correct_patch_button.setText(self.lang.get('correct_patch_btn')).addGUITooltip(self.lang.get('correct_patch_tooltip'))
        self.check_patch_button.setText(self.lang.get('check_patch_btn')).addGUITooltip(self.lang.get('check_patch_tooltip'))
        self.check_code_button.setText(self.lang.get('check_code_btn')).addGUITooltip(self.lang.get('check_code_tooltip'))
        self.test_run_button.setText(self.lang.get('test_run_btn')).addGUITooltip(self.lang.get('test_run_tooltip'))
        self.run_button.setText(self.lang.get('execute_patch_btn')).addGUITooltip(self.lang.get('execute_patch_tooltip'))
        self.load_patch_button.setText(self.lang.get('load_patch_btn')).addGUITooltip(self.lang.get('load_patch_tooltip'))

    def project_folder_changed(self, root_path):
        qs_widget = self.quick_settings_panel.accordions.get('dev_patcher', (None, None))[1]
        if qs_widget and hasattr(qs_widget, 'project_folder_changed'):
            qs_widget.project_folder_changed(root_path)
    
    def _open_examples_dialog(self):
        # Path to examples directory: .../dev_patcher/examples
        # Go up one level from 'gui' to 'dev_patcher'
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        examples_path = os.path.join(base_dir, "examples")
    
        dialog = ExamplesDialog(self, examples_path)
        if dialog.exec():
            content = dialog.get_content()
            if content:
                self.patch_input.setPlainText(content)
                self.patcher_log_output.appendPlainText(self.lang.get('example_patch_loaded'))
        