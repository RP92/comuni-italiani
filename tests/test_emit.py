import json
from pathlib import Path
from comuni_italiani.emit import emit

COMUNI = [{
    "nome": "Torino", "nomeAltraLingua": None, "codice": "001272",
    "codiceCatastale": "L219", "sigla": "TO", "cap": ["10121","10122"],
    "capoluogo": True, "popolazione": 848196, "superficie": 130.06,
    "coordinate": {"lat": 45.07, "lng": 7.68},
    "zona": {"nome": "Nord-ovest", "codice": "1"},
    "regione": {"nome": "Piemonte", "codice": "01"},
    "provincia": {"nome": "Torino", "codice": "001", "sigla": "TO", "tipo": "citta-metropolitana"},
}]

def test_emit_writes_all_formats(tmp_path):
    emit(COMUNI, tmp_path)
    data = json.loads((tmp_path / "comuni.json").read_text(encoding="utf-8"))
    assert data == COMUNI
    assert (tmp_path / "comuni.csv").exists()
    nd = (tmp_path / "comuni.ndjson").read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(nd[0])["codice"] == "001272"
    reg = json.loads((tmp_path / "regioni" / "piemonte.json").read_text(encoding="utf-8"))
    assert reg[0]["nome"] == "Torino"

def test_emit_csv_flattens_cap(tmp_path):
    emit(COMUNI, tmp_path)
    csv_text = (tmp_path / "comuni.csv").read_text(encoding="utf-8")
    assert '"10121,10122"' in csv_text or "10121,10122" in csv_text
