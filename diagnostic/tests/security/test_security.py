import unittest
import os
import json
import tempfile
import urllib.request
import shutil
from systems.security.manager import SecurityManager
from systems.security.ipc_server import SecurityIPCServer

class TestSecuritySystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="elai_sec_test_")
        self.sm = SecurityManager(self.temp_dir)
        
    def tearDown(self):
        self.sm.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_setup_and_verify(self):
        self.assertFalse(self.sm.is_setup)
        self.sm.setup("mypassword", "1", "2")
        self.assertTrue(self.sm.is_setup)
        
        self.assertTrue(self.sm.verify("mypassword"))
        self.assertFalse(self.sm.verify("wrongpassword"))

    def test_02_ipc_server_start_stop(self):
        self.sm.start_ipc()
        port = self.sm.get_ipc_port()
        self.assertGreater(port, 0)
        
        req_data = json.dumps({'action': 'Test', 'details': 'TestDetails'}).encode('utf-8')
        req = urllib.request.Request(f'http://127.0.0.1:{port}', data=req_data, headers={'Content-Type': 'application/json'})
        
        # In a headless environment without QApplication, request_permission will default to auto-allow True
        resp = urllib.request.urlopen(req, timeout=5)
        self.assertEqual(resp.status, 200)
        resp_data = json.loads(resp.read().decode('utf-8'))
        self.assertTrue(resp_data['allow'])
        
        self.sm.stop_ipc()
        self.assertEqual(self.sm.get_ipc_port(), 0)

    def test_03_auditor_templates(self):
        from systems.security.auditor.python_hook import PYTHON_AUDITOR_TEMPLATE
        from systems.security.auditor.node_hook import NODE_AUDITOR_TEMPLATE
        from systems.security.auditor.web_hook import WEB_AUDITOR_TEMPLATE
        
        self.assertIn("__SANDBOX_ROOT__", PYTHON_AUDITOR_TEMPLATE)
        self.assertIn("__IPC_PORT__", PYTHON_AUDITOR_TEMPLATE)
        
        self.assertIn("__SANDBOX_ROOT__", NODE_AUDITOR_TEMPLATE)
        self.assertIn("__IPC_PORT__", NODE_AUDITOR_TEMPLATE)
        
        self.assertIn("__IPC_PORT__", WEB_AUDITOR_TEMPLATE)
        
if __name__ == '__main__':
    unittest.main()