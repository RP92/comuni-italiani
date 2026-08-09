import csv
from pathlib import Path
from comuni_italiani.parse.coordinate import parse_coordinate

def _rows():
    text = Path("tests/fixtures/coordinate.csv").read_text(encoding="utf-8")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))

def test_parse_coordinate_skips_blanks():
    out = parse_coordinate(_rows())
    assert out["001272"] == {"lat": 45.0703, "lng": 7.6869}
    assert "003999" not in out


def test_parse_coordinate_italian_decimal_comma():
    rows = [{"codice": "001272", "lat": "45,0732891", "lng": "7,6806958"}]
    out = parse_coordinate(rows)
    assert out["001272"] == {"lat": 45.0732891, "lng": 7.6806958}
