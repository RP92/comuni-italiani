import pytest
from pathlib import Path
from comuni_italiani.validate import validate

SCHEMA = Path("data/schema.json")

def _c(codice, cap):
    return {
        "nome": "X", "nomeAltraLingua": None, "codice": codice,
        "codiceCatastale": "L219", "sigla": "TO", "cap": cap,
        "capoluogo": False, "popolazione": 1, "superficie": 1.0,
        "coordinate": None,
        "zona": {"nome": "Nord-ovest", "codice": "1"},
        "regione": {"nome": "Piemonte", "codice": "01"},
        "provincia": {"nome": "Torino", "codice": "001", "sigla": "TO", "tipo": "provincia"},
    }

def test_validate_reports_coverage():
    comuni = [_c("001272", ["10121"]), _c("002158", [])]
    report = validate(comuni, SCHEMA, min_count=1, max_count=10)
    assert report["count"] == 2
    assert report["cap_coverage"] == 0.5

def test_validate_rejects_duplicate_codice():
    comuni = [_c("001272", ["10121"]), _c("001272", ["10122"])]
    with pytest.raises(ValueError, match="duplicate"):
        validate(comuni, SCHEMA, min_count=1, max_count=10)

def test_validate_rejects_count_out_of_range():
    with pytest.raises(ValueError, match="count"):
        validate([_c("001272", [])], SCHEMA, min_count=7000, max_count=8200)
