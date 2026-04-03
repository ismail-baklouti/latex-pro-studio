"""Minimal Zotero client using API key + user id.

This client supports listing items (metadata) and fetching BibTeX for individual items.
It expects the Zotero API key to have appropriate permissions for read/write depending on operations.
"""
import requests
from typing import List, Dict


class ZoteroClient:
    BASE = "https://api.zotero.org"

    def __init__(self, user_id: str = None, api_key: str = None):
        self.user_id = user_id
        self.api_key = api_key
        self.detected = False

    def is_configured(self) -> bool:
        return bool(self.user_id and self.api_key)

    def _headers(self):
        headers = {
            'Zotero-API-Version': '3'
        }
        if self.api_key:
            # Zotero accepts API keys via 'Authorization: Bearer' for personal keys
            # and via 'Zotero-API-Key' header in some contexts. Provide both.
            headers['Authorization'] = f'Bearer {self.api_key}'
            headers['Zotero-API-Key'] = self.api_key
        return headers

    def configure_with_key(self, api_key: str) -> bool:
        """Set API key and attempt to detect the user_id automatically.

        Returns True if a user_id was detected and client is configured.
        """
        self.api_key = api_key
        # Try to call the Keys settings endpoint which may return owner info
        try:
            url = f"{self.BASE}/keys/{api_key}/settings"
            r = requests.get(url, headers=self._headers(), timeout=8)
            if r.status_code == 200:
                obj = r.json()
                # Some Zotero setups include 'userID' or 'user' in returned settings
                uid = obj.get('userID') or obj.get('user', {}).get('userID')
                if uid:
                    self.user_id = str(uid)
                    self.detected = True
                    return True
        except Exception:
            pass

        # Fallback: attempt to discover the user by calling the /keys endpoint (best-effort)
        try:
            url2 = f"{self.BASE}/keys"
            r2 = requests.get(url2, headers=self._headers(), timeout=8)
            if r2.status_code == 200:
                # If API returns a list, try to find an entry that matches our key
                try:
                    items = r2.json()
                    for it in items:
                        if it.get('key') == api_key and 'userID' in it:
                            self.user_id = str(it['userID'])
                            self.detected = True
                            return True
                except Exception:
                    pass
        except Exception:
            pass

        # Could not detect automatically; keep api_key set and return False
        return False

    def list_items(self, limit=25, query: str = None) -> List[Dict]:
        """Returns a list of item metadata dicts (contains 'key' and 'data')."""
        if not self.is_configured():
            return []

        params = {'limit': limit}
        if query:
            params['q'] = query

        url = f"{self.BASE}/users/{self.user_id}/items"
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return []

    def get_bibtex_for_item(self, item_key: str) -> str:
        """Fetches the BibTeX representation for a single Zotero item."""
        if not self.is_configured():
            return None

        url = f"{self.BASE}/users/{self.user_id}/items/{item_key}"
        params = {'format': 'bibtex'}
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=10)
            r.raise_for_status()
            return r.text
        except Exception:
            return None

    def delete_item(self, item_key: str) -> bool:
        """Delete an item (requires write permission on the API key)."""
        if not self.is_configured():
            return False

        url = f"{self.BASE}/users/{self.user_id}/items/{item_key}"
        try:
            r = requests.delete(url, headers=self._headers(), timeout=10)
            return r.status_code in (200, 204)
        except Exception:
            return False
