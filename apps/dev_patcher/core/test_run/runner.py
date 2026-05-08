import os
import tempfile
import shutil
from systems.security.auditor.python_hook import PYTHON_AUDITOR_TEMPLATE
from systems.security.auditor.node_hook import NODE_AUDITOR_TEMPLATE
from systems.security.auditor.web_hook import WEB_AUDITOR_TEMPLATE

from systems.fs.os_bridge.sandbox import OSSandbox


class TestRunner:
    """
    Orchestrates the sandbox environment for a test run.
    """
    def __init__(self, vfs, project_root, context=None):
        self.vfs = vfs
        self.project_root = project_root
        self.context = context
        self.temp_dir = None

    def prepare(self) -> str:
        import uuid
        import posixpath
        temp_project_dir = os.path.join(self.project_root, '.temp_project')
        os.makedirs(temp_project_dir, exist_ok=True)
        self.temp_dir = os.path.join(temp_project_dir, f"test_run_{uuid.uuid4().hex[:8]}")
        os.makedirs(self.temp_dir, exist_ok=True)

        from systems.os.platform import is_windows
        import subprocess

        modified_files = {}
        modified_dirs = set()
        for file_path in self.vfs.modified_paths:
            if self.vfs.exists(file_path) and not self.vfs.is_dir(file_path):
                rel_path = os.path.relpath(file_path, self.vfs.root).replace('\\', '/')
                modified_files[rel_path] = self.vfs.read_bytes(file_path)
                parent = posixpath.dirname(rel_path)
                while parent and parent != '.':
                    modified_dirs.add(parent)
                    parent = posixpath.dirname(parent)

        def link_or_copy(src, dst, is_dir):
            if is_dir:
                if is_windows():
                    res = subprocess.run(['cmd', '/c', 'mklink', '/J', dst, src], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if res.returncode != 0:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    try:
                        os.symlink(src, dst, target_is_directory=True)
                    except OSError:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                try:
                    os.link(src, dst)
                except OSError:
                    shutil.copy2(src, dst)

        def build_tree(current_rel_path):
            current_abs_src = os.path.join(self.project_root, current_rel_path)
            current_abs_dst = os.path.join(self.temp_dir, current_rel_path)
            os.makedirs(current_abs_dst, exist_ok=True)

            try:
                items = os.listdir(current_abs_src)
            except OSError:
                return

            for item in items:
                if item == '.temp_project': continue
                item_rel = posixpath.join(current_rel_path, item).strip('/')
                src_item = os.path.join(self.project_root, item_rel)
                dst_item = os.path.join(self.temp_dir, item_rel)

                if os.path.isdir(src_item):
                    if item_rel in modified_dirs:
                        build_tree(item_rel)
                    else:
                        link_or_copy(src_item, dst_item, is_dir=True)
                else:
                    if item_rel not in modified_files:
                        link_or_copy(src_item, dst_item, is_dir=False)

        build_tree("")

        for rel_path, content in modified_files.items():
            dst_file = os.path.join(self.temp_dir, os.path.normpath(rel_path))
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            with open(dst_file, 'wb') as f_out:
                f_out.write(content)

        # 3. Inject auditors
        if self.context and hasattr(self.context, 'security_manager'):
            sm = self.context.security_manager
            sm.start_ipc()
            port = sm.get_ipc_port()
            
            # Enable Trusted Mode if user provided password previously
            is_trusted = getattr(self.context.security_manager, 'is_trusted_session', False)

            py_hook = PYTHON_AUDITOR_TEMPLATE.replace("__SANDBOX_ROOT__", self.temp_dir.replace('\\', '\\\\')).replace("__IPC_PORT__", str(port))
            if is_trusted:
                py_hook = "import sys\n# TRUSTED MODE ACTIVE - LAYER 2 DISABLED\n"
            with open(os.path.join(self.temp_dir, "sitecustomize.py"), "w", encoding="utf-8") as f:
                f.write(py_hook)

            node_hook = NODE_AUDITOR_TEMPLATE.replace("__SANDBOX_ROOT__", self.temp_dir.replace('\\', '\\\\')).replace("__IPC_PORT__", str(port))
            with open(os.path.join(self.temp_dir, "_elai_node_auditor.js"), "w", encoding="utf-8") as f:
                f.write(node_hook)
                
            web_hook = WEB_AUDITOR_TEMPLATE.replace("__IPC_PORT__", str(port))
            with open(os.path.join(self.temp_dir, "_elai_web_auditor.js"), "w", encoding="utf-8") as f:
                js_code = web_hook.replace("<script>", "").replace("</script>", "")
                f.write(js_code)

        return self.temp_dir

    def cleanup(self) -> None:
        if self.context and hasattr(self.context, 'security_manager'):
            self.context.security_manager.stop_ipc()
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)