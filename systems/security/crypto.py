import hashlib
import base64

class CryptoPatterns:
    PATTERNS = {
        '1': 'SHA-256',
        '2': 'SHA-512',
        '3': 'MD5 (Salted Double Hash)',
        '4': 'Base64 + SHA-256',
        '5': 'Reverse + SHA-512'
    }

    @staticmethod
    def apply_pattern(password: str, pattern_id: str, salt: str) -> str:
        if pattern_id == '1':
            return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        elif pattern_id == '2':
            return hashlib.sha512((password + salt).encode('utf-8')).hexdigest()
        elif pattern_id == '3':
            return hashlib.md5((salt + password + salt).encode('utf-8')).hexdigest()
        elif pattern_id == '4':
            b64 = base64.b64encode(password.encode('utf-8')).decode('utf-8')
            return hashlib.sha256((b64 + salt).encode('utf-8')).hexdigest()
        elif pattern_id == '5':
            rev = password[::-1]
            return hashlib.sha512((rev + salt).encode('utf-8')).hexdigest()
        return password

    @staticmethod
    def hash_password(password: str, p1: str, p2: str, salt: str) -> str:
        step1 = CryptoPatterns.apply_pattern(password, p1, salt)
        step2 = CryptoPatterns.apply_pattern(step1, p2, salt)
        return step2