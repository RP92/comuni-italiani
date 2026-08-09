from pathlib import Path
import requests

# Some public sources (e.g. istat.it) reject the default python-requests
# User-Agent, so the real session presents a browser-like UA.
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

def fetch(url, cache_path, *, session=None, force=False):
    cache_path = Path(cache_path)
    if cache_path.exists() and not force:
        return cache_path
    if session is None:
        session = requests.Session()
        session.headers["User-Agent"] = _UA
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(resp.content)
    return cache_path
