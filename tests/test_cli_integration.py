# tests/test_cli_integration.py
import json
import tomllib
from pathlib import Path
from comuni_italiani.cli import build

def test_build_end_to_end(tmp_path):
    config = tomllib.loads(Path("tests/fixtures/sources.toml").read_text(encoding="utf-8"))
    out = tmp_path / "data"
    report = build(config, cache_dir=tmp_path / "cache", out_dir=out, offline=True)
    assert report["count"] == 2
    data = json.loads((out / "comuni.json").read_text(encoding="utf-8"))
    torino = next(c for c in data if c["codice"] == "001272")
    assert torino["popolazione"] == 848196
    assert torino["superficie"] == 130.06
    assert torino["cap"] == ["10121", "10122"]
    assert torino["coordinate"] == {"lat": 45.0703, "lng": 7.6869}
    assert (out / "regioni" / "piemonte.json").exists()
    assert (out / "quality-report.json").exists()


def test_build_bridges_catastale_keyed_source(tmp_path):
    import json
    from comuni_italiani.cli import build
    coord = tmp_path / "coord_cat.csv"
    # Source keyed by Belfiore code (like Garda), NOT by ISTAT codice.
    coord.write_text("codice_belfiore;lat;lon\nL219;45,07;7,68\n", encoding="utf-8")
    config = {
        "anagrafica": {"path": "tests/fixtures/istat_anagrafica.csv", "delimiter": ";", "encoding": "utf-8"},
        "popolazione": {"path": "tests/fixtures/popolazione.csv", "delimiter": ";"},
        "superficie": {"path": "tests/fixtures/superficie.csv", "delimiter": ";"},
        "coordinate": {"path": str(coord), "delimiter": ";", "key_by": "codiceCatastale",
                       "columns": {"codice": "codice_belfiore", "lat": "lat", "lng": "lon"}},
        "cap": {"path": "tests/fixtures/cap.csv", "delimiter": ";"},
    }
    out = tmp_path / "data"
    build(config, cache_dir=tmp_path / "c", out_dir=out, offline=True)
    d = json.loads((out / "comuni.json").read_text(encoding="utf-8"))
    torino = next(c for c in d if c["codice"] == "001272")  # Belfiore L219 -> ISTAT 001272
    assert torino["coordinate"] == {"lat": 45.07, "lng": 7.68}
