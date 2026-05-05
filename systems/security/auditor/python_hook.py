PYTHON_AUDITOR_TEMPLATE = """
import sys
import os
import json
import urllib.request
import threading

SANDBOX_ROOT = r"__SANDBOX_ROOT__"
IPC_PORT = __IPC_PORT__

_tls = threading.local()

def request_permission(action, details):
    _tls.in_ipc = True
    try:
        req = urllib.request.Request(f'http://127.0.0.1:{IPC_PORT}',
                                     data=json.dumps({'action': action, 'details': details}).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req, timeout=65) # 60s for GUI timeout + 5s buffer
        return json.loads(resp.read().decode())['allow']
    except Exception as e:
        print(f"IPC Error: {e}", file=sys.stderr)
        return False
    finally:
        _tls.in_ipc = False

def is_safe_path(path):
    try:
        if isinstance(path, int): return True
        abs_path = os.path.abspath(path)
        abs_sandbox = os.path.abspath(SANDBOX_ROOT)
        return abs_path.startswith(abs_sandbox)
    except:
        return False

def _safe_str(obj):
    try:
        return str(obj)
    except RecursionError:
        return "<unstringable object>"

def audit_hook(event, args):
    if getattr(_tls, 'in_ipc', False):
        return

    if event in ("os.system", "subprocess.Popen"):
        if not request_permission("Execute Command", _safe_str(args)):
            print(f"\033[91m🚫 [ELAI-AUDITOR-BLOCK] Blocked command: {args}\033[0m", file=sys.stderr)
            raise PermissionError("ELAI Security: Execution blocked by user.")
    elif event in ("socket.connect", "socket.getaddrinfo"):
        try:
            host = None
            port = None
            if isinstance(args[0], tuple):
                host, port = args[0][:2]
            elif len(args) >= 2:
                host, port = args[0], args[1]
            if str(host) in ("127.0.0.1", "localhost") and str(port) == str(IPC_PORT):
                return
        except:
            pass

        if not request_permission("Network Access", _safe_str(args)):
            print(f"\033[91m🚫 [ELAI-AUDITOR-BLOCK] Blocked network: {args}\033[0m", file=sys.stderr)
            raise PermissionError("ELAI Security: Network access blocked by user.")
    elif event == "urllib.Request":
        url = _safe_str(args[0])
        if f"127.0.0.1:{IPC_PORT}" in url or f"localhost:{IPC_PORT}" in url:
            return

        if not request_permission("Network Request", url):
            raise PermissionError("ELAI Security: Network request blocked by user.")
    elif event in ("os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.chmod", "os.chown"):
        if args and not is_safe_path(args[0]):
            if not request_permission("Modify File/Dir", _safe_str(args[0])):
                raise PermissionError("ELAI Security: Modification outside sandbox blocked.")
    elif event == "open":
        path, mode, flags = args
        if mode is not None and ('w' in mode or 'a' in mode or '+' in mode):
            if not is_safe_path(path):
                if not request_permission("Write to File", _safe_str(path)):
                    raise PermissionError("ELAI Security: Writing outside sandbox blocked.")

sys.addaudithook(audit_hook)
"""