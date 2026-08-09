import csv
from pathlib import Path
from comuni_italiani.parse.superficie import parse_superficie

def _rows():
    text = Path("tests/fixtures/superficie.csv").read_text(encoding="utf-8")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))

def test_parse_superficie():
    out = parse_superficie(_rows())
    assert out == {"001272": 130.06, "002158": 79.78}
