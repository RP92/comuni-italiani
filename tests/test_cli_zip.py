import csv, io, zipfile
from pathlib import Path
from comuni_italiani.cli import _read_rows

def _make_zip(tmp_path, member, csv_text):
    zpath = tmp_path / "src.zip"
    with zipfile.ZipFile(zpath, "w") as z:
        z.writestr(member, csv_text)
    return zpath

def test_read_rows_from_zip_with_member(tmp_path):
    zpath = _make_zip(tmp_path, "data.csv", "codice;popolazione\n001272;848196\n")
    spec = {"path": str(zpath), "member": "data.csv", "delimiter": ";", "encoding": "utf-8"}
    rows = _read_rows(spec, tmp_path / "cache", offline=True)
    assert rows[0]["codice"] == "001272"
    assert rows[0]["popolazione"] == "848196"

def test_read_rows_from_zip_single_member_autodetect(tmp_path):
    zpath = _make_zip(tmp_path, "only.csv", "codice;lat;lng\n001272;45.07;7.68\n")
    spec = {"path": str(zpath), "delimiter": ";"}  # no member; single csv -> autodetect
    rows = _read_rows(spec, tmp_path / "cache", offline=True)
    assert rows[0]["lat"] == "45.07"

def test_read_rows_plain_csv_still_works(tmp_path):
    p = tmp_path / "plain.csv"
    p.write_text("codice;cap\n001272;10121\n", encoding="utf-8")
    spec = {"path": str(p), "delimiter": ";"}
    rows = _read_rows(spec, tmp_path / "cache", offline=True)
    assert rows[0]["cap"] == "10121"
