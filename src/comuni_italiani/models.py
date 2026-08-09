import re
import unicodedata

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z]", "", s.lower())

_TIPO_RULES = [
    ("cittametropolitana", "citta-metropolitana"),
    ("liberoconsorzio", "libero-consorzio"),
    ("provinciaautonoma", "provincia-autonoma"),
    ("provincia", "provincia"),
]

def normalize_tipo(raw: str) -> str:
    key = _norm(raw)
    for needle, value in _TIPO_RULES:
        if needle in key:
            return value
    raise ValueError(f"Unknown provincia tipo: {raw!r}")
