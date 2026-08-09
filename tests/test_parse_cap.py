import csv
from pathlib import Path
from comuni_italiani.parse.cap import parse_cap

def _rows():
    text = Path("tests/fixtures/cap.csv").read_text(encoding="utf-8")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))

def test_parse_cap_dedups_and_sorts():
    out = parse_cap(_rows())
    assert out["001272"] == ["10121", "10122"]
    assert out["002158"] == ["13100"]

def test_parse_cap_ignores_malformed():
    rows = [{"codice": "009999", "cap": "abc"}, {"codice": "009999", "cap": "1234"}]
    assert parse_cap(rows) == {}
