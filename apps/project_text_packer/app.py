import os
import datetime
from PySide6.QtCore import Signal, QThread, QObject
from PySide6.QtWidgets import QMessageBox

from systems.project.ignore_handler import IgnoreHandler

class Worker(QObject):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, packer_instance, overwrite=False):
        super().__init__()
        self.packer = packer_instance
        self.overwrite = overwrite
        self.settings = self.packer.load_quick_settings()
    
    def run(self):
        try:
            p = self.packer
            opts = self.settings
    
            # Output paths
            base_name = p.project_name
            created_files_list = []
    
            # --- 1. Collect and Prepare Data ---
            self.progress.emit(p.lang.get('packer_log_collecting_files'))
            file_list = p.collect_files(p.root_path, p.ignore_handler)
    
            self.progress.emit(p.lang.get('packer_log_building_tree'))
            tree_lines = p._build_tree_recursive(p.root_path, p.ignore_handler)
    
            # Prepare Tree Content
            timestamp_str = ""
            if opts['add_timestamp']:
                timestamp_str = f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
            tree_content = f"{timestamp_str}Project: {p.project_name}\n" + "\n".join(tree_lines)
    
            # --- 2. Remove Old Files ---
            if self.overwrite:
                self.progress.emit(p.lang.get('packer_removing_old_files_log'))
                self._cleanup_old_files(p.output_dir, base_name)
    
            # --- 3. Write Output ---
            self.progress.emit(p.lang.get('packer_log_writing_pack'))
    
            if opts['one_file']:
                # Combined Mode: Tree is at the top of the pack file
                self._write_split_aware(
                    file_list, 
                    p.output_dir, 
                    f"{base_name}_project_pack", 
                    created_files_list,
                    tree_header=tree_content,
                    split=opts['split_on_limit']
                )
            else:
                # Separate Mode: Write tree to separate file, then pack files
                tree_path = os.path.join(p.output_dir, f"{base_name}_tree.txt")
                with open(tree_path, 'w', encoding='utf-8') as f:
                    f.write(tree_content)
                created_files_list.append(tree_path)
                self.progress.emit(f"Tree saved to: {os.path.basename(tree_path)}")
    
                self._write_split_aware(
                    file_list, 
                    p.output_dir, 
                    f"{base_name}_project_pack",
                    created_files_list, 
                    tree_header=None,
                    split=opts['split_on_limit']
                )
    
            # Emit successful list of files
            self.finished.emit("\n".join(created_files_list))
        except Exception as e:
            import traceback
            self.error.emit(f"{e}\n{traceback.format_exc()}")
    
    def _cleanup_old_files(self, output_dir, base_name):
        # Removes _project_pack.txt, _tree.txt and any _partX.txt variants
        patterns = [f"{base_name}_tree.txt", f"{base_name}_project_pack.txt"]
    
        # Simple cleanup for standard files
        for fname in patterns:
            fpath = os.path.join(output_dir, fname)
            if os.path.exists(fpath):
                os.remove(fpath)
    
        # Cleanup for parts
        for fname in os.listdir(output_dir):
            if fname.startswith(f"{base_name}_project_pack") and fname.endswith(".txt"):
                os.remove(os.path.join(output_dir, fname))
    
    def _write_split_aware(self, file_list, output_dir, base_filename, created_files_list, tree_header=None, split=False):
        """
        Writes files to output, handling splitting and merging tree header.
        """
        MAX_SIZE = int(self.settings.get('split_size_mb', 1.0) * 1024 * 1024)

        current_part = 1
    
        # Helper to open file
        def open_part(part_num):
            suffix = f"_part{part_num}" if split else ""
            fname = f"{base_filename}{suffix}.txt" if split else f"{base_filename}.txt"
            path = os.path.join(output_dir, fname)
            return open(path, 'w', encoding='utf-8'), fname, path
    
        current_file, current_fname, current_path = open_part(current_part)
        current_size = 0
    
        # Write Tree Header if provided (only for part 1)
        if tree_header:
            current_file.write(tree_header + "\n\n")
            current_size += len(tree_header.encode('utf-8')) + 2
    
        # Iterate files
        for full_path, rel_path in sorted(file_list, key=lambda p: p[1]):
            self.progress.emit(f"  -> {rel_path.replace(os.sep, '/')}")
    
            # Prepare content buffer for this file
            file_buffer = []
            file_buffer.append(f"#//> {self.packer.project_name}/{rel_path.replace(os.sep, '/')}:\n")
    
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as src:
                    lines = src.readlines()
    
                if not lines:
                    file_buffer.append(f"1| {self.packer.lang.get('packer_empty_file_comment')}\n")
                else:
                    max_line_num_width = len(str(len(lines)))
                    for idx, line in enumerate(lines, start=1):
                        line_num_str = str(idx).rjust(max_line_num_width)
                        file_buffer.append(f"{line_num_str}| {line.rstrip()}\n")
            except Exception as e:
                file_buffer.append(f"1| <!-- ERROR reading file: {e} -->\n")
    
            file_buffer.append("\n" + "="*80 + "\n\n")
    
            full_text = "".join(file_buffer)
            text_size = len(full_text.encode('utf-8'))
    
            # Check limit
            if split and (current_size + text_size > MAX_SIZE):
                # Close current
                current_file.close()
                created_files_list.append(current_path)
                self.progress.emit(f"  [Info] Limit reached. Saved {current_fname}")
    
                # Start new part
                current_part += 1
                current_file, current_fname, current_path = open_part(current_part)
                current_size = 0
    
            current_file.write(full_text)
            current_size += text_size
    
        current_file.close()
        created_files_list.append(current_path)
        if split:
            self.progress.emit(f"  [Info] Saved {current_fname}")
        
            # If we didn't actually split (only 1 part), rename back to normal
            if current_part == 1:
                normal_fname = f"{base_filename}.txt"
                normal_path = os.path.join(output_dir, normal_fname)
        
                try:
                    # Rename part1 to normal
                    if os.path.exists(normal_path):
                        os.remove(normal_path)
                    os.rename(current_path, normal_path)
        
                    # Update created list
                    created_files_list.pop()
                    created_files_list.append(normal_path)
                    self.progress.emit(f"  [Info] Renamed {current_fname} to {normal_fname} (size < limit)")
                except OSError as e:
                    self.progress.emit(f"  [Warning] Failed to rename single part: {e}")


class ProjectTextPackerApp:

    def __init__(self, context):
        self.context = context
        self.lang = context.lang
        self.settings_manager = context.settings_manager
        self.widget = None
        self.worker_thread = None

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

    def start_pack(self):
        # Update root path from main window if available (Dynamic linkage)
        if hasattr(self.context, 'main_window') and self.context.main_window:
             self.root_path = self.context.main_window.root_path

        output_dir = self.widget.output_dir_input.currentText().strip()

        if not self.root_path:
            QMessageBox.warning(self.widget, self.lang.get('patch_load_error_title'), self.lang.get('project_folder_missing_error'))
            return

        if not output_dir:
            QMessageBox.warning(self.widget, self.lang.get('patch_load_error_title'), self.lang.get('packer_output_dir_not_selected_error'))
            return

        self.project_name = os.path.basename(os.path.normpath(self.root_path))
        self.output_dir = output_dir # Store for worker

        # Save path to history
        self.widget.save_recent_path(self.output_dir)

        # Basic overwrite check (rough)
        base_path = os.path.join(output_dir, f"{self.project_name}_project_pack")
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
            g_dirs, g_files, _ = self.settings_manager.get_ignore_lists()
            ignore_dirs, ignore_files = g_dirs, g_files

        self.ignore_handler = IgnoreHandler(ignore_dirs, ignore_files, context='packer')
        
        self.worker_thread = QThread()
        self.worker = Worker(self, overwrite=should_overwrite)
        self.worker.moveToThread(self.worker_thread)

        self.worker.finished.connect(self.widget.on_packing_finished)
        self.worker.error.connect(self.widget.on_packing_error)
        self.worker.progress.connect(self.widget.log_box.appendPlainText)

        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

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

    def collect_files(self, root_dir, handler):
        file_list = []
        supported_extensions = self.get_supported_extensions()
        for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
            dirnames[:] = [d for d in dirnames if not handler.is_ignored(d, is_dir=True)]
            for file in filenames:
                if handler.is_ignored(file, is_dir=False):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if not ext or ext in supported_extensions:
                    full_path = os.path.join(dirpath, file)
                    rel_path = os.path.relpath(full_path, root_dir)
                    file_list.append((full_path, rel_path))
        return file_list

    def write_tree(self, tree_lines, output_file, project_name):
        # Legacy method kept if needed, but logic moved to Worker
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Project: {project_name}\n")
            f.write("\n".join(tree_lines))

    def _build_tree_recursive(self, dir_path: str, handler: IgnoreHandler, prefix=""):
        tree = []
        try:
            items_in_dir = sorted(os.listdir(dir_path))
        except PermissionError:
            return [prefix + "└── [Access Denied]"]
        processed_items = []
        for item in items_in_dir:
            is_dir = os.path.isdir(os.path.join(dir_path, item))
            is_ignored_item = handler.is_ignored(item, is_dir=is_dir)
            processed_items.append({'name': item, 'is_dir': is_dir, 'is_ignored': is_ignored_item})
        for i, item_data in enumerate(processed_items):
            is_last = (i == len(processed_items) - 1)
            connector = "└── " if is_last else "├── "
            item_name = item_data['name']
            is_dir = item_data['is_dir']
            is_ignored = item_data['is_ignored']
            display_name = item_name
            if is_dir:
                display_name += "/"
            if is_ignored:
                display_name += " [...]"
            tree.append(prefix + connector + display_name)
            if is_dir and not is_ignored:
                item_full_path = os.path.join(dir_path, item_name)
                extension = "    " if is_last else "│   "
                tree.extend(self._build_tree_recursive(item_full_path, handler, prefix + extension))
        return tree