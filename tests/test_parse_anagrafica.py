import csv
from pathlib import Path
from comuni_italiani.parse.anagrafica import parse_anagrafica

def _rows():
    text = Path("tests/fixtures/istat_anagrafica.csv").read_text(encoding="utf-8")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))

def test_parses_torino():
    out = {c["codice"]: c for c in parse_anagrafica(_rows())}
    t = out["001272"]
    assert t["nome"] == "Torino"
    assert t["nomeAltraLingua"] is None
    assert t["codiceCatastale"] == "L219"
    assert t["sigla"] == "TO"
    assert t["capoluogo"] is True
    assert t["zona"] == {"nome": "Nord-ovest", "codice": "1"}
    assert t["regione"] == {"nome": "Piemonte", "codice": "01"}
    assert t["provincia"] == {"nome": "Torino", "codice": "001", "sigla": "TO", "tipo": "citta-metropolitana"}

def test_row_count():
    assert len(parse_anagrafica(_rows())) == 2
