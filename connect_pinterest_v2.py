"""Connect the Daniel Mason Pinterest profile using a local OAuth callback.

Python 3.10+, standard library only. Never logs secrets or publishes content.
"""
import base64
import getpass
import json
import os
from pathlib import Path
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

APP_ID = "1622682"
EXPECTED_USER = "danielmason77"
REDIRECT_URI = "http://localhost:8765/"
SCOPES = {"boards:read", "boards:write", "pins:read", "pins:write", "user_accounts:read"}
OUTPUT = Path(__file__).resolve().parent / ".pinterest_credentials_v2.json"


class ConnectionError(Exception):
    """An error safe to display without raw API responses or credentials."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(path, authorization, form=None):
    headers = {"Authorization": authorization, "Accept": "application/json"}
    body = None
    if form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(
        "https://api.pinterest.com/v5" + path, data=body, headers=headers,
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
            result = json.load(response)
        if not isinstance(result, dict):
            raise ConnectionError("Unexpected Pinterest response.")
        return result
    except urllib.error.HTTPError as error:
        raise ConnectionError("Pinterest returned HTTP " + str(error.code) + ".") from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise ConnectionError("Pinterest network or response error. Please retry.") from None


def authorization_url(state):
    return "https://www.pinterest.com/oauth/?" + urllib.parse.urlencode({
        "client_id": APP_ID, "redirect_uri": REDIRECT_URI,
        "response_type": "code", "scope": ",".join(sorted(SCOPES)), "state": state,
    })


def callback_result(path, state):
    parsed = urllib.parse.urlsplit(path)
    if parsed.path != "/":
        return None
    try:
        query = urllib.parse.parse_qs(parsed.query, max_num_fields=10)
    except ValueError:
        return None
    received = query.get("state", [])
    if len(received) != 1 or not secrets.compare_digest(received[0].encode(), state.encode()):
        return None
    if "error" in query:
        return {"error": True}
    codes = query.get("code", [])
    if len(codes) != 1 or not codes[0]:
        return None
    return {"code": codes[0]}


def receive_code(state, open_browser=webbrowser.open, timeout_seconds=600):
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Request URLs contain authorization codes: never log them.

        def do_GET(self):
            if self.headers.get("Host", "").lower() != "localhost:8765":
                self.send_error(400)
                return
            accepted = callback_result(self.path, state)
            if accepted is None:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid callback. Continue in the original Pinterest window.")
                return
            result.update(accepted)
            html = (b"<!doctype html><meta charset=utf-8><title>Daniel Mason connection</title>"
                    b"<script>history.replaceState(null,'','/')</script>"
                    b"<h1>Authorization received</h1><p>Return to the connection program. "
                    b"It will verify the profile before saving any tokens.</p>")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(html)

    try:
        server = HTTPServer(("127.0.0.1", 8765), Callback)
    except OSError:
        raise ConnectionError("Port 8765 is unavailable. Close the other connection program.") from None
    with server:
        server.timeout = 1
        url = authorization_url(state)
        print("In Pinterest, select @" + EXPECTED_USER + " and review the requested permissions.")
        if not open_browser(url):
            print("Open this authorization link in your browser:\n" + url)
        deadline = time.monotonic() + timeout_seconds
        while not result and time.monotonic() < deadline:
            server.handle_request()
    if not result:
        raise ConnectionError("Authorization timed out after 10 minutes. Run the program again.")
    if "error" in result:
        raise ConnectionError("Pinterest authorization was declined or failed. No tokens saved.")
    return result["code"]


def validate_tokens(tokens, get_account):
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")
    if not isinstance(access, str) or not access or not isinstance(refresh, str) or not refresh:
        raise ConnectionError("Access/refresh token missing. No credentials saved.")
    scope = tokens.get("scope", "")
    granted = set(scope.replace(",", " ").split()) if isinstance(scope, str) else set()
    missing = SCOPES - granted
    if missing:
        raise ConnectionError("Missing permissions: " + ", ".join(sorted(missing)) + ". No credentials saved.")
    account = get_account(access)
    username = str(account.get("username", "")).lstrip("@").casefold()
    if username != EXPECTED_USER.casefold():
        raise ConnectionError("The authorized profile is not @" + EXPECTED_USER + ". No credentials saved.")
    return {**tokens, "username": EXPECTED_USER, "app_id": APP_ID, "saved_at": int(time.time())}


def save_credentials(credentials):
    # Exclusive creation avoids overwriting an existing connection or following a symlink.
    descriptor = os.open(OUTPUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(credentials, handle, indent=2)
        handle.write("\n")


def main():
    print("Daniel Mason Pinterest OAuth connection (App " + APP_ID + ")")
    print("Registered Redirect URI must be exactly: " + REDIRECT_URI)
    print("No Pins, boards, ads, or campaigns will be created.")
    if OUTPUT.exists():
        raise ConnectionError("A credentials file already exists. Move it securely before reconnecting.")
    secret = getpass.getpass("Paste the App secret key for app 1622682 (hidden): ").strip()
    if not secret:
        raise ConnectionError("App secret is required.")
    state = secrets.token_urlsafe(32)
    code = receive_code(state)
    basic = base64.b64encode((APP_ID + ":" + secret).encode()).decode("ascii")
    tokens = request_json("/oauth/token", "Basic " + basic, {
        "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI,
    })
    verified = validate_tokens(tokens, lambda token: request_json("/user_account", "Bearer " + token))
    save_credentials(verified)
    print("SUCCESS: @" + EXPECTED_USER + " verified; requested permissions granted.")
    print("Credentials saved locally beside this script in .pinterest_credentials_v2.json.")
    print("Keep that file private. Never commit it or paste its contents into chat.")
    print("Next: update the GitHub access-token secret, then run the connection check.")
    print("Trial access still limits created Pins/boards to creator-only visibility.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled. No publishing performed.")
        raise SystemExit(1)
    except (ConnectionError, OSError) as error:
        # OSError may include local file paths but never request bodies or tokens.
        print("Connection failed: " + str(error))
        raise SystemExit(1)
