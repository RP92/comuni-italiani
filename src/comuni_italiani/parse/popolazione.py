from typing import Iterable

def parse_popolazione(rows: Iterable[dict]) -> dict[str, int]:
    out = {}
    for r in rows:
        codice = r["codice"].strip()
        raw = (r.get("popolazione") or "").strip().replace(".", "")
        if raw:
            out[codice] = int(raw)
    return out
