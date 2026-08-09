import csv
from pathlib import Path
from comuni_italiani.parse.popolazione import parse_popolazione

def _rows():
    text = Path("tests/fixtures/popolazione.csv").read_text(encoding="utf-8")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))

def test_parse_popolazione():
    out = parse_popolazione(_rows())
    assert out == {"001272": 848196, "002158": 46552}
