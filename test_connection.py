import unittest
import urllib.parse
from connect_pinterest import callback_result, validate_tokens, ConnectionError, SCOPES, authorization_url


class ConnectionSecurityTests(unittest.TestCase):
    def test_rejects_missing_wrong_and_duplicate_state(self):
        for query in ("code=x", "code=x&state=wrong", "code=x&state=s&state=s", "code=x&state=%C3%A9"):
            self.assertIsNone(callback_result("/?" + query, "s"))

    def test_only_accepts_one_code_on_exact_callback_path(self):
        self.assertIsNone(callback_result("/other?code=x&state=s", "s"))
        self.assertIsNone(callback_result("/?code=x&code=y&state=s", "s"))
        self.assertEqual(callback_result("/?code=x&state=s", "s"), {"code": "x"})
        self.assertEqual(callback_result("/?error=access_denied&state=s", "s"), {"error": True})

    def test_wrong_profile_and_incomplete_permissions_are_not_saved(self):
        tokens = {"access_token": "test-access", "refresh_token": "test-refresh", "scope": " ".join(SCOPES)}
        with self.assertRaises(ConnectionError):
            validate_tokens(tokens, lambda _: {"username": "other-profile"})
        with self.assertRaises(ConnectionError):
            validate_tokens({**tokens, "scope": "boards:read"}, lambda _: {"username": "danielmason77"})
        result = validate_tokens(tokens, lambda _: {"username": "danielmason77"})
        self.assertEqual(result["username"], "danielmason77")

    def test_authorization_request_targets_fixed_app_and_callback(self):
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(authorization_url("test-state")).query)
        self.assertEqual(params["client_id"], ["1622682"])
        self.assertEqual(params["redirect_uri"], ["http://localhost:8765/"])
        self.assertEqual(params["state"], ["test-state"])
        self.assertEqual(set(params["scope"][0].split(",")), SCOPES)


if __name__ == "__main__":
    unittest.main()
