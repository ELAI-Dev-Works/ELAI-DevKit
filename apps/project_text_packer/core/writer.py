import os

class PackWriter:
    @staticmethod
    def cleanup_old_files(out_fs, base_name):
        patterns =[f"{base_name}_tree.txt", f"{base_name}_project_pack.txt"]
        for fname in patterns:
            if out_fs.exists(fname):
                out_fs.delete(fname)
        try:
            for fname in out_fs.listdir(""):
                if fname.startswith(f"{base_name}_project_pack") and fname.endswith(".txt"):
                    out_fs.delete(fname)
        except Exception:
            pass

    @staticmethod
    def write_split_aware(fs, out_fs, file_list, base_filename, created_files_list, opts, project_name, lang, tree_header=None, split=False):
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
            file_buffer.append(f"#//> {project_name}/{rel_path.replace(os.sep, '/')}:\n")
            try:
                content = fs.read(rel_path)
                if not content:
                    file_buffer.append(f"1| {lang.get('packer_empty_file_comment')}\n")
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
                yield f"[Info] Renamed {current_fname} to {normal_fname} (size < limit)"
            except Exception as e:
                yield f"  [Warning] Failed to rename single part: {e}"