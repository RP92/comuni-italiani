from typing import Iterable

def parse_superficie(rows: Iterable[dict]) -> dict[str, float]:
    out = {}
    for r in rows:
        codice = r["codice"].strip()
        # NOTE: assumes Italian number format — '.' as thousands separator, ',' as decimal
        # (e.g. "1.234,56" → 1234.56). Verify this assumption against the real ISTAT
        # superficie file before changing source-column mappings.
        raw = (r.get("superficie") or "").strip().replace(".", "").replace(",", ".")
        if raw:
            out[codice] = float(raw)
    return out
