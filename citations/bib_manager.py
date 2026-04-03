import re
from pathlib import Path


def _extract_key(bibtex_entry: str) -> str:
    m = re.search(r"@\w+\{\s*([^,\s]+)", bibtex_entry)
    return m.group(1) if m else None


def add_entry(bib_path, bibtex_entry: str) -> bool:
    """Append a BibTeX entry to the bib file if the key does not already exist.

    Returns True if added, False if key existed or on error.
    """
    try:
        bib_path = Path(bib_path)
        bib_path.parent.mkdir(parents=True, exist_ok=True)
        key = _extract_key(bibtex_entry)
        if not key:
            return False

        if bib_path.exists():
            content = bib_path.read_text(encoding='utf-8')
            if re.search(r"@\w+\{\s*" + re.escape(key) + r"\s*,", content):
                return False
            with bib_path.open('a', encoding='utf-8') as f:
                f.write('\n' + bibtex_entry.strip() + '\n')
                return True
        else:
            bib_path.write_text(bibtex_entry.strip() + '\n', encoding='utf-8')
            return True
    except Exception:
        return False


def remove_entry(bib_path, cite_key: str) -> bool:
    """Remove an entry by citation key from the bib file.

    Returns True if removed, False if not found or on error.
    """
    try:
        bib_path = Path(bib_path)
        if not bib_path.exists():
            return False

        content = bib_path.read_text(encoding='utf-8')

        # Match any @type{key, ... } including nested braces by naive approach
        pattern = re.compile(r"@\w+\{\s*" + re.escape(cite_key) + r"\s*,.*?(?=\n@|\Z)", re.S)
        new_content, n = pattern.subn('', content)
        if n == 0:
            return False

        bib_path.write_text(new_content.strip() + '\n', encoding='utf-8')
        return True
    except Exception:
        return False
