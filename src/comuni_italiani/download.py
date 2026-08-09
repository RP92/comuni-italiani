from pathlib import Path
import requests

def fetch(url, cache_path, *, session=None, force=False):
    cache_path = Path(cache_path)
    if cache_path.exists() and not force:
        return cache_path
    session = session or requests.Session()
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(resp.content)
    return cache_path
