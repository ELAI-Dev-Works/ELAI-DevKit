import os
import datetime
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from systems.project.ignore_handler import IgnoreHandler



class ProjectTextPackerApp:

    def __init__(self, context):
        self.context = context
        self.lang = context.lang
        self.settings_manager = context.settings_manager
        self.widget = None

        self.app_root_path = getattr(self.context, 'app_root_path', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

        # Compatibility property for old code that might check root_path
        # In V2, we try to get it from the context's main window if available
        self.root_path = None
        if hasattr(self.context, 'main_window') and self.context.main_window:
             self.root_path = self.context.main_window.root_path

    def set_widget(self, widget):
        self.widget = widget

    def load_quick_settings(self):
        settings = self.settings_manager.get_setting(['apps', 'project_text_packer', 'quick'], {})
        # The settings are now nested under 'Options' from the default_settings TOML string
        options = settings.get('Options', {})
        return {
            'one_file': options.get('one_file', False),
            'add_timestamp': options.get('add_timestamp', True),
            'split_on_limit': options.get('split_on_limit', True),
            'split_size_mb': options.get('split_size_mb', 1.0)
        }

    def _cleanup_old_files(self, out_fs, base_name):
        patterns = [f"{base_name}_tree.txt", f"{base_name}_project_pack.txt"]
        for fname in patterns:
            if out_fs.exists(fname):
                out_fs.delete(fname)
        try:
            for fname in out_fs.listdir(""):
                if fname.startswith(f"{base_name}_project_pack") and fname.endswith(".txt"):
                    out_fs.delete(fname)
        except Exception:
            pass

    def _write_split_aware(self, fs, out_fs, file_list, base_filename, created_files_list, opts, tree_header=None, split=False):
        MAX_SIZE = int(opts.get('split_size_mb', 1.0) * 1024 * 1024)
        current_part = 1

        def get_fname(part_num):
            suffix = f"_part{part_num}" if split else ""
            return f"{base_filename}{suffix}.txt"

        current_fname = get_fname(current_part)
        current_content_buffer =[]
        current_size = 0

        if tree_header:
            current_content_buffer.append(tree_header + "\n\n")
            current_size += len((tree_header + "\n\n").encode('utf-8'))

        for full_path, rel_path in sorted(file_list, key=lambda p: p[1]):
            yield f"  -> {rel_path.replace(os.sep, '/')}"
            file_buffer =[]
            file_buffer.append(f"#//> {self.project_name}/{rel_path.replace(os.sep, '/')}:\n")
            try:
                content = fs.read(rel_path)
                if not content:
                    file_buffer.append(f"1| {self.lang.get('packer_empty_file_comment')}\n")
                else:
                    lines = content.splitlines()
                    max_line_num_width = len(str(len(lines)))
                    for idx, line in enumerate(lines, start=1):
                        line_num_str = str(idx).rjust(max_line_num_width)
                        file_buffer.append(f"{line_num_str}| {line}\n")
            except Exception as e:
                file_buffer.append(f"1| <!-- ERROR reading file: {e} -->\n")

            file_buffer.append("\n" + "="*80 + "\n\n")
            full_text = "".join(file_buffer)
            text_size = len(full_text.encode('utf-8'))

            if split and (current_size + text_size > MAX_SIZE):
                out_fs.write(current_fname, "".join(current_content_buffer))
                created_files_list.append(out_fs._to_abs(current_fname))
                yield f"[Info] Limit reached. Saved {current_fname}"
                current_part += 1
                current_fname = get_fname(current_part)
                current_content_buffer =[]
                current_size = 0

            current_content_buffer.append(full_text)
            current_size += text_size

        if current_content_buffer:
            out_fs.write(current_fname, "".join(current_content_buffer))
            created_files_list.append(out_fs._to_abs(current_fname))
            if split:
                yield f"  [Info] Saved {current_fname}"

        if split and current_part == 1:
            normal_fname = f"{base_filename}.txt"
            try:
                if out_fs.exists(normal_fname):
                    out_fs.delete(normal_fname)
                out_fs.rename(current_fname, normal_fname)
                created_files_list.pop()
                created_files_list.append(out_fs._to_abs(normal_fname))
                yield f"  [Info] Renamed {current_fname} to {normal_fname} (size < limit)"
            except Exception as e:
                yield f"  [Warning] Failed to rename single part: {e}"
    def start_pack(self):
        # Update root path from main window if available (Dynamic linkage)
        if hasattr(self.context, 'main_window') and self.context.main_window:
             self.root_path = self.context.main_window.root_path

        base_output_dir = self.widget.output_dir_input.currentText().strip()

        if not self.root_path:
            QMessageBox.warning(self.widget, self.lang.get('patch_load_error_title'), self.lang.get('project_folder_missing_error'))
            return

        if not base_output_dir:
            QMessageBox.warning(self.widget, self.lang.get('patch_load_error_title'), self.lang.get('packer_output_dir_not_selected_error'))
            return

        # Save the selected base path to history before modification
        self.widget.save_recent_path(base_output_dir)

        final_output_dir = base_output_dir
        category_path = self.widget.category_combo.currentData()
        if category_path:
            final_output_dir = os.path.normpath(os.path.join(base_output_dir, category_path))

        os.makedirs(final_output_dir, exist_ok=True)

        self.project_name = os.path.basename(os.path.normpath(self.root_path))
        self.output_dir = final_output_dir # Store the final, combined path for the worker

        # Basic overwrite check (rough)
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

        # Use combined ignore lists from MainWindow
        if hasattr(self.context, 'main_window') and self.context.main_window:
            ignore_dirs, ignore_files = self.context.main_window.get_combined_ignore_lists()
        else:
            # Fallback for standalone mode if context structure differs
            g_dirs, g_files, _, _, _ = self.settings_manager.get_ignore_lists()
            ignore_dirs, ignore_files = g_dirs, g_files

        self.ignore_handler = IgnoreHandler(ignore_dirs, ignore_files, context='packer')
        
        opts = self.load_quick_settings()
        fs = self.context.fs.get_fs(self.root_path)
        out_fs = self.context.fs.get_fs(self.output_dir)
        base_name = self.project_name

        def pack_task():
            created_files_list =[]
            yield self.lang.get('packer_log_collecting_files')
            file_list = self.collect_files(fs, self.ignore_handler)

            yield self.lang.get('packer_log_building_tree')
            tree_lines = self._build_tree_recursive(fs, "", self.ignore_handler)

            timestamp_str = ""
            if opts['add_timestamp']:
                import datetime
                timestamp_str = f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            tree_content = f"{timestamp_str}Project: {self.project_name}\n" + "\n".join(tree_lines)

            if should_overwrite:
                yield self.lang.get('packer_removing_old_files_log')
                self._cleanup_old_files(out_fs, base_name)

            yield self.lang.get('packer_log_writing_pack')

            if opts['one_file']:
                yield from self._write_split_aware(
                    fs, out_fs, file_list, f"{base_name}_project_pack",
                    created_files_list, opts, tree_header=tree_content, split=opts['split_on_limit']
                )
            else:
                tree_fname = f"{base_name}_tree.txt"
                out_fs.write(tree_fname, tree_content)
                created_files_list.append(out_fs._to_abs(tree_fname))
                yield f"Tree saved to: {tree_fname}"
                yield from self._write_split_aware(
                    fs, out_fs, file_list, f"{base_name}_project_pack",
                    created_files_list, opts, tree_header=None, split=opts['split_on_limit']
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

    def collect_files(self, fs, handler):
        import posixpath
        file_list = []
        supported_extensions = self.get_supported_extensions()
        for dirpath, dirnames, filenames in fs.walk(""):
            rel_dirpath = os.path.relpath(dirpath, fs.root).replace('\\', '/')
            if rel_dirpath == '.': rel_dirpath = ""

            dirnames[:] = [d for d in dirnames if not handler.is_ignored(d, is_dir=True)]
            for file in filenames:
                if handler.is_ignored(file, is_dir=False):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if not ext or ext in supported_extensions:
                    rel_path = posixpath.join(rel_dirpath, file).strip('/')
                    full_path = fs._to_abs(rel_path)
                    file_list.append((full_path, rel_path))
        return file_list

    def _build_tree_recursive(self, fs, dir_path_rel: str, handler: IgnoreHandler, prefix=""):
        import posixpath
        tree = []
        try:
            items_in_dir = sorted(fs.listdir(dir_path_rel))
        except PermissionError:
            return [prefix + "└── [Access Denied]"]
        except FileNotFoundError:
            return []

        processed_items = []
        for item in items_in_dir:
            item_rel = posixpath.join(dir_path_rel, item).strip('/')
            is_dir = fs.is_dir(item_rel)
            is_ignored_item = handler.is_ignored(item, is_dir=is_dir)
            processed_items.append({'name': item, 'is_dir': is_dir, 'is_ignored': is_ignored_item, 'rel': item_rel})

        for i, item_data in enumerate(processed_items):
            is_last = (i == len(processed_items) - 1)
            connector = "└── " if is_last else "├── "
            item_name = item_data['name']
            is_dir = item_data['is_dir']
            is_ignored = item_data['is_ignored']
            item_rel = item_data['rel']

            display_name = item_name
            if is_dir:
                display_name += "/"
            if is_ignored:
                display_name += " [...]"
            tree.append(prefix + connector + display_name)

            if is_dir and not is_ignored:
                extension = "    " if is_last else "│   "
                tree.extend(self._build_tree_recursive(fs, item_rel, handler, prefix + extension))
        return tree