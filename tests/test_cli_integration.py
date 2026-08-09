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
