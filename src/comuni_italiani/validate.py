import json
from pathlib import Path
from jsonschema import Draft202012Validator

def validate(comuni, schema_path, min_count=7000, max_count=8200):
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(comuni)

    count = len(comuni)
    if not (min_count <= count <= max_count):
        raise ValueError(f"comuni count {count} out of range [{min_count},{max_count}]")

    codici = [c["codice"] for c in comuni]
    dupes = {x for x in codici if codici.count(x) > 1}
    if dupes:
        raise ValueError(f"duplicate codice: {sorted(dupes)[:5]}")

    with_cap = sum(1 for c in comuni if c["cap"])
    return {
        "count": count,
        "cap_coverage": round(with_cap / count, 4) if count else 0.0,
        "errors": [],
    }
