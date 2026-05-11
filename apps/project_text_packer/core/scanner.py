import os
import posixpath

class FileScanner:
    @staticmethod
    def collect_files(fs, handler, supported_extensions):
        file_list =[]
        for dirpath, dirnames, filenames in fs.walk(""):
            rel_dirpath = os.path.relpath(dirpath, fs.root).replace('\\', '/')
            if rel_dirpath == '.': rel_dirpath = ""

            dirnames[:] =[d for d in dirnames if not handler.is_ignored(d, is_dir=True)]
            for file in filenames:
                if handler.is_ignored(file, is_dir=False):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if not ext or ext in supported_extensions:
                    rel_path = posixpath.join(rel_dirpath, file).strip('/')
                    full_path = fs._to_abs(rel_path)
                    file_list.append((full_path, rel_path))
        return file_list