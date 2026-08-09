from typing import Iterable


def _to_float(s: str) -> float:
    # Tolerate Italian decimal comma (e.g. "45,3593736" from the Garda source)
    return float(s.replace(",", "."))


def parse_coordinate(rows: Iterable[dict]) -> dict[str, dict]:
    out = {}
    for r in rows:
        codice = r["codice"].strip()
        lat = (r.get("lat") or "").strip()
        lng = (r.get("lng") or "").strip()
        if lat and lng:
            out[codice] = {"lat": _to_float(lat), "lng": _to_float(lng)}
    return out
