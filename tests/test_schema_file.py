import json
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA = Path("data/schema.json")

def test_schema_is_valid_jsonschema():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)

def test_schema_accepts_a_valid_comune():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    sample = [{
        "nome": "Torino", "nomeAltraLingua": None, "codice": "001272",
        "codiceCatastale": "L219", "sigla": "TO", "cap": ["10121"],
        "capoluogo": True, "popolazione": 848196, "superficie": 130.06,
        "coordinate": {"lat": 45.0703, "lng": 7.6869},
        "zona": {"nome": "Nord-ovest", "codice": "1"},
        "regione": {"nome": "Piemonte", "codice": "01"},
        "provincia": {"nome": "Torino", "codice": "001", "sigla": "TO", "tipo": "citta-metropolitana"},
    }]
    Draft202012Validator(schema).validate(sample)
