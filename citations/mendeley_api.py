"""
Latex Pro Studio - Mendeley API Client
Handles OAuth2 authentication and document synchronization.
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

import requests
import logging
import re
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MendeleyAPI:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.mendeley.com"
        self.redirect_uri = "http://localhost:8080"

    def get_auth_url(self) -> str:
        """Returns the URL the user needs to visit to log in."""
        return (
            f"{self.base_url}/oauth/authorize?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code&scope=all"
        )

    def exchange_code_for_token(self, code: str) -> bool:
        """Swaps the authorization code for an access token."""
        url = f"{self.base_url}/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                self.access_token = response.json().get("access_token")
                return True
            else:
                logger.error(f"Mendeley Token Exchange Failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Mendeley Auth Error: {e}")
            return False

    def fetch_all_documents(self) -> List[Dict]:
        """
        Fetches the user's library. Handles pagination automatically 
        if the library has more than 50 items.
        """
        if not self.access_token:
            return []

        documents = []
        url = f"{self.base_url}/documents"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {'view': 'all', 'limit': 50}

        while url:
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    for doc in data:
                        documents.append(self._format_document(doc))
                    
                    # Check for pagination links in headers
                    url = self._get_next_link(response.headers)
                    params = {} # The next link already contains params
                else:
                    logger.error(f"Mendeley Fetch Error: {response.status_code}")
                    break
            except Exception as e:
                logger.error(f"Mendeley Request Crash: {e}")
                break

        return documents

    def _format_document(self, doc: Dict) -> Dict:
        """Transforms Mendeley's JSON into a standard internal format."""
        # 1. Extract Author
        authors = doc.get('authors', [])
        author_str = "Unknown"
        last_name = "Unknown"
        if authors:
            last_name = authors[0].get('last_name', 'Unknown')
            author_str = f"{last_name}, {authors[0].get('first_name', '')}"
            if len(authors) > 1:
                author_str += " et al."

        # 2. Extract Year
        year = str(doc.get('year', 'n.d.'))

        # 3. Generate BibTeX Cite Key (e.g., Baklouti2024)
        clean_name = re.sub(r'\W+', '', last_name) # Remove spaces/special chars
        cite_key = f"{clean_name}{year}"

        return {
            "key": cite_key,
            "author": author_str,
            "year": year,
            "title": doc.get('title', 'No Title'),
            "source": "Mendeley",
            "type": self._map_type(doc.get('type', 'journal'))
        }

    def _map_type(self, m_type: str) -> str:
        """Maps Mendeley document types to standard BibTeX types."""
        type_map = {
            'journal': 'article',
            'book_section': 'incollection',
            'book': 'book',
            'thesis': 'phdthesis',
            'conference_proceedings': 'inproceedings',
            'web_page': 'misc'
        }
        return type_map.get(m_type, 'article')

    def _get_next_link(self, headers: Dict) -> Optional[str]:
        """Parses the 'Link' header for pagination."""
        link_header = headers.get('Link')
        if not link_header:
            return None
        
        # Example: <url>; rel="next"
        match = re.search(r'<(.*?)>; rel="next"', link_header)
        return match.group(1) if match else None