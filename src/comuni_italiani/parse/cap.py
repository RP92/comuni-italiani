import re
from typing import Iterable

_CAP_RE = re.compile(r"^\d{5}$")

def parse_cap(rows: Iterable[dict]) -> dict[str, list[str]]:
    acc: dict[str, set] = {}
    for r in rows:
        codice = r["codice"].strip()
        cap = (r.get("cap") or "").strip()
        if _CAP_RE.match(cap):
            acc.setdefault(codice, set()).add(cap)
    return {k: sorted(v) for k, v in acc.items()}
