"""Minimal Mendeley client placeholder.

Mendeley API requires OAuth2 flows. This client accepts a pre-obtained access token
and provides simple list/get/delete wrappers. This module implements a simple
interactive OAuth2 authorization code flow for desktop apps using a temporary
local HTTP server to receive the redirect and capture the authorization code.
"""
import requests
import webbrowser
import threading
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
import time


class MendeleyClient:
    BASE = "https://api.mendeley.com"
    AUTHORIZE = "https://api.mendeley.com/oauth/authorize"
    TOKEN = "https://api.mendeley.com/oauth/token"

    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.refresh_token = None
        self.expires_at = None

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def _headers(self):
        return {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}

    def list_documents(self, limit=25):
        if not self.is_configured():
            return []
        try:
            r = requests.get(f"{self.BASE}/documents", headers=self._headers(), params={'limit': limit}, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return []

    def get_document(self, doc_id):
        if not self.is_configured():
            return None
        try:
            r = requests.get(f"{self.BASE}/documents/{doc_id}", headers=self._headers(), timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    # --- OAuth2 flow helpers ---
    def get_authorize_url(self, client_id: str, redirect_uri: str, scope: str = 'all', state: str = None):
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope
        }
        if state:
            params['state'] = state
        return f"{self.AUTHORIZE}?" + urlparse.urlencode(params)

    def exchange_code_for_token(self, client_id: str, client_secret: str, code: str, redirect_uri: str) -> bool:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }
        try:
            r = requests.post(self.TOKEN, data=data, timeout=10)
            r.raise_for_status()
            obj = r.json()
            self.access_token = obj.get('access_token')
            self.refresh_token = obj.get('refresh_token')
            expires_in = obj.get('expires_in')
            if expires_in:
                self.expires_at = time.time() + int(expires_in)
            return True
        except Exception:
            return False

    def authenticate_interactive(self, client_id: str, client_secret: str, scope: str = 'all', port: int = 8086, timeout: int = 120) -> bool:
        """Performs an interactive OAuth flow: opens browser, starts local server, exchanges code."""
        # Find a free port if requested port is 0
        host = '127.0.0.1'
        if port == 0:
            with socket.socket() as s:
                s.bind((host, 0))
                port = s.getsockname()[1]

        redirect_uri = f'http://{host}:{port}/callback'
        url = self.get_authorize_url(client_id, redirect_uri, scope)

        code_container = {}

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self_inner):
                parsed = urlparse.urlparse(self_inner.path)
                qs = urlparse.parse_qs(parsed.query)
                if 'code' in qs:
                    code_container['code'] = qs['code'][0]
                    self_inner.send_response(200)
                    self_inner.send_header('Content-Type', 'text/html')
                    self_inner.end_headers()
                    self_inner.wfile.write(b"<html><body><h3>Authorization received. You may close this window.</h3></body></html>")
                else:
                    self_inner.send_response(400)
                    self_inner.end_headers()

            def log_message(self_inner, format, *args):
                return

        httpd = HTTPServer((host, port), _Handler)

        # Start server in background thread
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()

        # Open browser to authorize
        webbrowser.open(url)

        # Wait for code or timeout
        start = time.time()
        while time.time() - start < timeout:
            if 'code' in code_container:
                break
            time.sleep(0.5)

        httpd.shutdown()

        code = code_container.get('code')
        if not code:
            return False

        return self.exchange_code_for_token(client_id, client_secret, code, redirect_uri)
