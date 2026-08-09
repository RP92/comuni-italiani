import csv
import io
import json
from pathlib import Path
from comuni_italiani.slug import slugify

CSV_COLUMNS = [
    "codice", "nome", "nomeAltraLingua", "codiceCatastale", "sigla",
    "cap", "capoluogo", "popolazione", "superficie",
    "coordinate.lat", "coordinate.lng",
    "zona.nome", "zona.codice", "regione.nome", "regione.codice",
    "provincia.nome", "provincia.codice", "provincia.sigla", "provincia.tipo",
]

def _flat(c: dict) -> dict:
    coord = c["coordinate"] or {}
    return {
        "codice": c["codice"], "nome": c["nome"],
        "nomeAltraLingua": c["nomeAltraLingua"] or "",
        "codiceCatastale": c["codiceCatastale"] or "",
        "sigla": c["sigla"] or "",
        "cap": ",".join(c["cap"]),
        "capoluogo": "1" if c["capoluogo"] else "0",
        "popolazione": c["popolazione"] if c["popolazione"] is not None else "",
        "superficie": c["superficie"] if c["superficie"] is not None else "",
        "coordinate.lat": coord.get("lat", ""),
        "coordinate.lng": coord.get("lng", ""),
        "zona.nome": c["zona"]["nome"], "zona.codice": c["zona"]["codice"],
        "regione.nome": c["regione"]["nome"], "regione.codice": c["regione"]["codice"],
        "provincia.nome": c["provincia"]["nome"], "provincia.codice": c["provincia"]["codice"],
        "provincia.sigla": c["provincia"]["sigla"] or "",
        "provincia.tipo": c["provincia"]["tipo"],
    }

def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def emit(comuni: list[dict], outdir: Path) -> None:
    outdir = Path(outdir)
    (outdir / "regioni").mkdir(parents=True, exist_ok=True)
    _write_json(outdir / "comuni.json", comuni)

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS)
    w.writeheader()
    for c in comuni:
        w.writerow(_flat(c))
    (outdir / "comuni.csv").write_text(buf.getvalue(), encoding="utf-8")

    with (outdir / "comuni.ndjson").open("w", encoding="utf-8") as f:
        for c in comuni:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    by_reg: dict[str, list] = {}
    for c in comuni:
        by_reg.setdefault(slugify(c["regione"]["nome"]), []).append(c)
    for slug, items in by_reg.items():
        _write_json(outdir / "regioni" / f"{slug}.json", items)
