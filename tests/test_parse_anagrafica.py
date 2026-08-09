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


def test_numeric_tipo_codes_and_header_whitespace():
    # Real ISTAT: numeric tipologia codes + header cells with embedded newline / trailing space.
    row = {
        "Codice Comune formato alfanumerico": "082053",
        "Denominazione in italiano": "Palermo",
        "Denominazione altra lingua": "",
        "Codice Catastale del comune": "G273",
        "Sigla automobilistica": "PA",
        "Flag Comune capoluogo di provincia/città metropolitana/libero consorzio": "1",
        "Ripartizione geografica": "Isole",
        "Codice Ripartizione Geografica": "5",
        "Denominazione Regione": "Sicilia",
        "Codice Regione": "19",
        "Denominazione dell'Unità territoriale sovracomunale \n(valida a fini statistici)": "Palermo",
        "Codice dell'Unità territoriale sovracomunale \n(valida a fini statistici)": "082",
        "Tipologia di Unità territoriale sovracomunale ": "3",
    }
    out = parse_anagrafica([row])[0]
    assert out["nome"] == "Palermo"
    assert out["provincia"]["nome"] == "Palermo"
    assert out["provincia"]["tipo"] == "citta-metropolitana"


def test_numeric_tipo_code_5_is_decentramento_regionale():
    row = {
        "Codice Comune formato alfanumerico": "031007",
        "Denominazione in italiano": "Gorizia",
        "Codice Catastale del comune": "E098",
        "Sigla automobilistica": "GO",
        "Flag Comune capoluogo di provincia/città metropolitana/libero consorzio": "1",
        "Ripartizione geografica": "Nord-est",
        "Codice Ripartizione Geografica": "2",
        "Denominazione Regione": "Friuli-Venezia Giulia",
        "Codice Regione": "06",
        "Denominazione dell'Unità territoriale sovracomunale (valida a fini statistici)": "Gorizia",
        "Codice dell'Unità territoriale sovracomunale (valida a fini statistici)": "031",
        "Tipologia di Unità territoriale sovracomunale": "5",
    }
    assert parse_anagrafica([row])[0]["provincia"]["tipo"] == "decentramento-regionale"
