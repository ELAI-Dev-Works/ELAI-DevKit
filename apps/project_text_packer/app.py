import os
import datetime
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from systems.project.ignore_handler import IgnoreHandler
from .core.scanner import FileScanner
from .core.tree_builder import TreeBuilder
from .core.writer import PackWriter

class ProjectTextPackerApp:
    def __init__(self, context):
        self.context = context
        self.lang = context.lang
        self.settings_manager = context.settings_manager
        self.widget = None

        self.app_root_path = getattr(self.context, 'app_root_path', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

        self.root_path = None
        if hasattr(self.context, 'main_window') and self.context.main_window:
             self.root_path = self.context.main_window.root_path

    def set_widget(self, widget):
        self.widget = widget

    def load_quick_settings(self):
        settings = self.settings_manager.get_setting(['apps', 'project_text_packer', 'quick'], {})
        options = settings.get('Options', {})
        return {
            'one_file': options.get('one_file', False),
            'add_timestamp': options.get('add_timestamp', True),
            'split_on_limit': options.get('split_on_limit', True),
            'split_size_mb': options.get('split_size_mb', 1.0)
        }

    def get_supported_extensions(self):
        settings = self.settings_manager.get_setting(['apps', 'project_text_packer', 'settings'], {})
        extensions_str = settings.get('supported_extensions', '')
        exts = set()
        for line in extensions_str.splitlines():
            line = line.strip()
            if not line or line.startswith('['):
                continue
            for ext in line.split():
                ext = ext.strip()
                if ext:
                    exts.add(ext)
        return exts

    def start_pack(self):
        if hasattr(self.context, 'main_window') and self.context.main_window:
             self.root_path = self.context.main_window.root_path

        base_output_dir = self.widget.output_dir_input.currentText().strip()

        if not self.root_path:
            QMessageBox.warning(self.widget, self.lang.get('patch_load_error_title'), self.lang.get('project_folder_missing_error'))
            return

        if not base_output_dir:
            QMessageBox.warning(self.widget, self.lang.get('patch_load_error_title'), self.lang.get('packer_output_dir_not_selected_error'))
            return

        self.widget.save_recent_path(base_output_dir)

        final_output_dir = base_output_dir
        category_path = self.widget.category_combo.currentData()
        if category_path:
            final_output_dir = os.path.normpath(os.path.join(base_output_dir, category_path))

        os.makedirs(final_output_dir, exist_ok=True)

        self.project_name = os.path.basename(os.path.normpath(self.root_path))
        self.output_dir = final_output_dir 

        base_path = os.path.join(self.output_dir, f"{self.project_name}_project_pack")
        if os.path.exists(f"{base_path}.txt") or os.path.exists(f"{base_path}_part1.txt"):
            reply = QMessageBox.question(
                self.widget, self.lang.get('packer_overwrite_title'), self.lang.get('packer_overwrite_message'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                self.widget.log_box.appendPlainText(self.lang.get('packer_status_cancelled'))
                return
            should_overwrite = True
        else:
            should_overwrite = False

        self.widget.start_button.setEnabled(False)
        self.widget.progress_indicator.start(0, self.lang.get('packer_status_packing'))
        self.widget.log_box.clear()

        if hasattr(self.context, 'main_window') and self.context.main_window:
            ignore_dirs, ignore_files = self.context.main_window.get_combined_ignore_lists()
        else:
            g_dirs, g_files, _, _, _ = self.settings_manager.get_ignore_lists()
            ignore_dirs, ignore_files = g_dirs, g_files

        self.ignore_handler = IgnoreHandler(ignore_dirs, ignore_files, context='packer')
        
        opts = self.load_quick_settings()
        supported_extensions = self.get_supported_extensions()
        fs = self.context.fs.get_fs(self.root_path)
        out_fs = self.context.fs.get_fs(self.output_dir)
        base_name = self.project_name

        def pack_task():
            created_files_list = []
            yield self.lang.get('packer_log_collecting_files')
            file_list = FileScanner.collect_files(fs, self.ignore_handler, supported_extensions)

            yield self.lang.get('packer_log_building_tree')
            tree_lines = TreeBuilder.build(fs, "", self.ignore_handler)

            timestamp_str = ""
            if opts['add_timestamp']:
                timestamp_str = f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            tree_content = f"{timestamp_str}Project: {self.project_name}\n" + "\n".join(tree_lines)

            if should_overwrite:
                yield self.lang.get('packer_removing_old_files_log')
                PackWriter.cleanup_old_files(out_fs, base_name)

            yield self.lang.get('packer_log_writing_pack')

            if opts['one_file']:
                yield from PackWriter.write_split_aware(
                    fs, out_fs, file_list, f"{base_name}_project_pack",
                    created_files_list, opts, self.project_name, self.lang, tree_header=tree_content, split=opts['split_on_limit']
                )
            else:
                tree_fname = f"{base_name}_tree.txt"
                out_fs.write(tree_fname, tree_content)
                created_files_list.append(out_fs._to_abs(tree_fname))
                yield f"Tree saved to: {tree_fname}"
                yield from PackWriter.write_split_aware(
                    fs, out_fs, file_list, f"{base_name}_project_pack",
                    created_files_list, opts, self.project_name, self.lang, tree_header=None, split=opts['split_on_limit']
                )

            return "\n".join(created_files_list)

        tc = self.context.async_thread_manager.thread
        tc.run_in_background(
            pack_task,
            callback=self.widget.on_packing_finished,
            error_callback=lambda e: self.widget.on_packing_error(str(e)),
            yield_callback=self.widget.log_box.appendPlainText,
            use_qt=True
        )