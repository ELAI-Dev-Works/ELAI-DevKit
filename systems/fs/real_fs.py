import os
import shutil
from .base_fs import BaseFileSystem

class RealFileSystem(BaseFileSystem):
    def exists(self, path): return os.path.exists(self._to_abs(path))
    def is_dir(self, path): return os.path.isdir(self._to_abs(path))
    def listdir(self, path: str): return os.listdir(self._to_abs(path))
    def read(self, path):
        abs_path = self._to_abs(path)
        if self.memory and os.path.exists(abs_path):
            mtime = os.path.getmtime(abs_path)
            fsize = os.path.getsize(abs_path)
            cache = self.memory.get_cache('fs_reads', max_items=2000, max_size_bytes=200 * 1024 * 1024)
            cache_key = f"rfs_read:{abs_path}"
            cached_item = cache.get(cache_key)
            if cached_item and cached_item['mtime'] == mtime and cached_item.get('fsize') == fsize:
                return cached_item['content']

            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Manually specify size to accurately track memory usage
            item_size = len(content.encode('utf-8', errors='ignore'))
            cache.set(cache_key, {'mtime': mtime, 'fsize': fsize, 'content': content}, tags=[f"file:{abs_path}"], size=item_size)
            return content
        else:
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f: return f.read()

    def read_bytes(self, path):
        abs_path = self._to_abs(path)
        if self.memory and os.path.exists(abs_path):
            mtime = os.path.getmtime(abs_path)
            fsize = os.path.getsize(abs_path)
            cache = self.memory.get_cache('fs_reads_bytes', max_items=2000, max_size_bytes=200 * 1024 * 1024)
            cache_key = f"rfs_read_bytes:{abs_path}"
            cached_item = cache.get(cache_key)
            if cached_item and cached_item['mtime'] == mtime and cached_item.get('fsize') == fsize:
                return cached_item['content']

            with open(abs_path, 'rb') as f:
                content = f.read()

            cache.set(cache_key, {'mtime': mtime, 'fsize': fsize, 'content': content}, tags=[f"file:{abs_path}"], size=len(content))
            return content
        else:
            with open(abs_path, 'rb') as f: return f.read()
    def write(self, path, content: str):
        if isinstance(content, bytes):
            raise TypeError("write expects str, received bytes. Use write_bytes.")
        abs_path = self._to_abs(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f: f.write(content)
    def write_bytes(self, path, content: bytes):
        abs_path = self._to_abs(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'wb') as f: f.write(content)
    def makedirs(self, path): os.makedirs(self._to_abs(path), exist_ok=True)
    def move(self, src, dst): shutil.move(self._to_abs(src), self._to_abs(dst))
    def copy(self, src, dst):
        abs_src, abs_dst = self._to_abs(src), self._to_abs(dst)
        if self.is_dir(src): shutil.copytree(abs_src, abs_dst, dirs_exist_ok=True)
        else: shutil.copy2(abs_src, abs_dst)
    def rename(self, src, dst): os.rename(self._to_abs(src), self._to_abs(dst))
    def delete(self, path):
        abs_path = self._to_abs(path)
        if self.is_dir(path): shutil.rmtree(abs_path)
        elif os.path.exists(abs_path): os.remove(abs_path)
    def walk(self, top): return os.walk(self._to_abs(top))