import unittest
import os
import tempfile
import shutil
from systems.security.manager import SecurityManager

class TestSecurityRules(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="elai_sec_rules_")
        self.sm = SecurityManager(self.temp_dir)

    def tearDown(self):
        self.sm.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_rules_no_allow_deny(self):
        result = self.sm._check_rules("Write to File", "/some/path")
        self.assertIsNone(result)

    def test_global_allow_rule(self):
        self.sm.rules["Global"]["allow"] = {"Write to File": ["/some/path"]}
        result = self.sm._check_rules("Write to File", "/some/path")
        self.assertTrue(result)

    def test_project_deny_rule(self):
        self.sm.current_project_name = "test_project"
        self.sm.rules["test_project"] = {"allow": {}, "deny": {"Execute Command": ["rm -rf"]}}
        result = self.sm._check_rules("Execute Command", "rm -rf")
        self.assertFalse(result)

    def test_global_deny_overrides_project_allow(self):
        self.sm.current_project_name = "test_project"
        self.sm.rules["Global"]["deny"] = {"Network Access": ["evil.com"]}
        self.sm.rules["test_project"] = {"allow": {"Network Access": ["evil.com"]}, "deny": {}}
        result = self.sm._check_rules("Network Access", "evil.com")
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()