import re
import unicodedata

def slugify(name: str) -> str:
    """Lowercase ASCII hyphen-slug. Bilingual 'IT/DE' -> part before '/'."""
    base = name.split("/", 1)[0]
    ascii_str = (
        unicodedata.normalize("NFKD", base)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    ascii_str = ascii_str.lower()
    ascii_str = re.sub(r"[^a-z0-9]+", "-", ascii_str)
    return ascii_str.strip("-")
