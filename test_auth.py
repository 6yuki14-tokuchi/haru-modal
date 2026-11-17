import base64
import unittest
from protected_haru import accepts_authorization

class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.password = "x" * 48
        self.header = "Basic " + base64.b64encode(("haru:" + self.password).encode()).decode()

    def test_correct_credentials(self):
        self.assertTrue(accepts_authorization(self.header, self.password))

    def test_missing_malformed_and_wrong_credentials(self):
        for value in [None, "", "Bearer token", "Basic abc", self.header + "x", "Basic 日本語"]:
            with self.subTest(value=value):
                self.assertFalse(accepts_authorization(value, self.password))

    def test_empty_and_short_passwords_fail_closed(self):
        for value in ["", "short", "x" * 31]:
            self.assertFalse(accepts_authorization(self.header, value))

if __name__ == "__main__":
    unittest.main()
