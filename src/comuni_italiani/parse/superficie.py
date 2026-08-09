from typing import Iterable

def parse_superficie(rows: Iterable[dict]) -> dict[str, float]:
    out = {}
    for r in rows:
        codice = r["codice"].strip()
        raw = (r.get("superficie") or "").strip().replace(".", "").replace(",", ".")
        if raw:
            out[codice] = float(raw)
    return out
