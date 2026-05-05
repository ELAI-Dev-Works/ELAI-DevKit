import unittest
from systems.security.crypto import CryptoPatterns

class TestCryptoPatterns(unittest.TestCase):
    def setUp(self):
        self.salt = "test_salt"
        self.pwd = "mypassword"

    def test_sha256(self):
        h = CryptoPatterns.apply_pattern(self.pwd, '1', self.salt)
        self.assertEqual(len(h), 64)  # SHA-256 hex is 64 chars

    def test_sha512(self):
        h = CryptoPatterns.apply_pattern(self.pwd, '2', self.salt)
        self.assertEqual(len(h), 128)  # SHA-512 hex is 128 chars

    def test_md5_double(self):
        h = CryptoPatterns.apply_pattern(self.pwd, '3', self.salt)
        self.assertEqual(len(h), 32)  # MD5 hex 32 chars

    def test_base64_sha256(self):
        h = CryptoPatterns.apply_pattern(self.pwd, '4', self.salt)
        self.assertEqual(len(h), 64)

    def test_reverse_sha512(self):
        h = CryptoPatterns.apply_pattern(self.pwd, '5', self.salt)
        self.assertEqual(len(h), 128)

    def test_hash_password_combination(self):
        final = CryptoPatterns.hash_password(self.pwd, '1', '2', self.salt)
        self.assertEqual(len(final), 128)
        self.assertNotEqual(final, self.pwd)

    def test_different_salts_produce_different(self):
        h1 = CryptoPatterns.hash_password(self.pwd, '1', '2', "salt1")
        h2 = CryptoPatterns.hash_password(self.pwd, '1', '2', "salt2")
        self.assertNotEqual(h1, h2)

if __name__ == '__main__':
    unittest.main()