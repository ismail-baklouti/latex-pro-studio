"""
Latex Pro Studio - Zotero API Client
Handles library synchronization using the pyzotero wrapper.
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

import logging
import re
from typing import List, Dict, Optional

# Optional Import Handling
ZOTERO_AVAILABLE = False
try:
    from pyzotero import zotero
    ZOTERO_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

class ZoteroAPI:
    def __init__(self, library_id: str, api_key: str, library_type: str = 'user'):
        """
        :param library_id: The Zotero User ID (found in Zotero settings).
        :param api_key: The API Key generated from zotero.org.
        :param library_type: 'user' or 'group'.
        """
        self.library_id = library_id
        self.api_key = api_key
        self.library_type = library_type
        self.client = None
        
        if ZOTERO_AVAILABLE and library_id and api_key:
            self.client = zotero.Zotero(self.library_id, self.library_type, self.api_key)

    def is_configured(self) -> bool:
        return self.client is not None

    def fetch_all_items(self, limit: int = 100) -> List[Dict]:
        """
        Fetches items from Zotero and converts them to the internal unified format.
        """
        if not self.client:
            logger.error("Zotero client not configured.")
            return []

        unified_items = []
        try:
            # Fetch top-level items (excluding attachments/notes)
            # pyzotero handles pagination automatically with top() or everything()
            items = self.client.top(limit=limit)
            
            for item in items:
                data = item.get('data', {})
                # Skip items that aren't actual publications (like notes)
                if data.get('itemType') in ['note', 'attachment']:
                    continue
                    
                unified_items.append(self._format_item(data))
                
        except Exception as e:
            logger.error(f"Zotero Fetch Failed: {e}")
            
        return unified_items

    def _format_item(self, data: Dict) -> Dict:
        """Transforms Zotero's JSON schema into the project's internal format."""
        
        # 1. Extract Author (Zotero uses 'creators' list)
        creators = data.get('creators', [])
        author_str = "Unknown"
        last_name = "Unknown"
        
        # Find the first creator who is an 'author'
        authors = [c for c in creators if c.get('creatorType') == 'author']
        if not authors and creators: # Fallback to any creator if no 'author' type exists
            authors = [creators[0]]
            
        if authors:
            last_name = authors[0].get('lastName', 'Unknown')
            first_name = authors[0].get('firstName', '')
            author_str = f"{last_name}, {first_name}"
            if len(authors) > 1:
                author_str += " et al."

        # 2. Extract Year (Zotero 'date' is often a full string like '2023-10-12')
        full_date = data.get('date', 'n.d.')
        year_match = re.search(r'\d{4}', full_date)
        year = year_match.group(0) if year_match else "nd"

        # 3. Generate BibTeX Cite Key (Standardized)
        clean_name = re.sub(r'\W+', '', last_name)
        cite_key = f"{clean_name.lower()}{year}"

        return {
            "key": cite_key,
            "author": author_str,
            "year": year,
            "title": data.get('title', 'No Title'),
            "source": "Zotero",
            "type": self._map_type(data.get('itemType', 'journalArticle'))
        }

    def _map_type(self, z_type: str) -> str:
        """Maps Zotero item types to standard BibTeX entry types."""
        type_map = {
            'journalArticle': 'article',
            'book': 'book',
            'bookSection': 'incollection',
            'conferencePaper': 'inproceedings',
            'thesis': 'phdthesis',
            'report': 'techreport',
            'webpage': 'misc'
        }
        return type_map.get(z_type, 'article')