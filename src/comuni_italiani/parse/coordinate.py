from typing import Iterable

def parse_coordinate(rows: Iterable[dict]) -> dict[str, dict]:
    out = {}
    for r in rows:
        codice = r["codice"].strip()
        lat = (r.get("lat") or "").strip()
        lng = (r.get("lng") or "").strip()
        if lat and lng:
            out[codice] = {"lat": float(lat), "lng": float(lng)}
    return out
