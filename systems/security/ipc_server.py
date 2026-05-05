import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class SecurityRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress HTTP logs to keep console clean
        
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data.decode('utf-8'))
            
            allow = self.server.security_manager.request_permission(
                req.get('action', 'Unknown'), 
                req.get('details', '')
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'allow': allow}).encode('utf-8'))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

class SecurityIPCServer:
    def __init__(self, security_manager):
        self.sm = security_manager
        self.server = None
        self.port = 0
        self.thread = None
        self._is_running = False

    def start(self):
        if self._is_running:
            return
        self.server = HTTPServer(('127.0.0.1', 0), SecurityRequestHandler)
        self.server.security_manager = self.sm
        self.port = self.server.server_port
        self._is_running = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self._is_running and self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)
            self._is_running = False
            self.server = None
            self.port = 0