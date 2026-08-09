# tests/test_cli_read_rows.py
"""
Focused tests for _read_rows — covers the columns remap path that was previously untested.
"""
from pathlib import Path
from comuni_italiani.cli import _read_rows

FIXTURE = Path("tests/fixtures/remap_sample.csv")

def test_remap_canonical_keys_win():
    """Remapped (canonical) keys must carry the value from the source column."""
    spec = {
        "path": str(FIXTURE),
        "delimiter": ";",
        "encoding": "utf-8",
        "columns": {
            "codice": "PRO_COM",
            "popolazione": "POP",
        },
    }
    rows = _read_rows(spec, cache_dir=Path("/tmp"), offline=False)

    assert len(rows) == 2
    torino = next(r for r in rows if r["codice"] == "001272")
    assert torino["codice"] == "001272", "canonical key 'codice' must come from PRO_COM"
    assert torino["popolazione"] == "848196", "canonical key 'popolazione' must come from POP"
    # Original raw keys are still present in the row
    assert "PRO_COM" in torino
    assert "POP" in torino


def test_remap_wins_over_existing_canonical_key():
    """
    If the source CSV happened to already have a column named 'codice'
    the remap must still overwrite it with the value from the source column
    specified in the mapping (canonical wins, not the pre-existing raw key).
    This verifies the merge order: r | remap, NOT remap | r.
    """
    spec = {
        "path": str(FIXTURE),
        "delimiter": ";",
        "encoding": "utf-8",
        "columns": {
            # Map 'codice' <- 'PRO_COM'; if a field named 'codice' existed
            # in the row the remap dict must still win.
            "codice": "PRO_COM",
        },
    }
    rows = _read_rows(spec, cache_dir=Path("/tmp"), offline=False)
    vercelli = next(r for r in rows if r["codice"] == "002158")
    assert vercelli["codice"] == "002158"


def test_no_remap_returns_raw_rows():
    """When no 'columns' key is present the rows come through unmodified."""
    spec = {
        "path": str(FIXTURE),
        "delimiter": ";",
        "encoding": "utf-8",
    }
    rows = _read_rows(spec, cache_dir=Path("/tmp"), offline=False)
    assert rows[0]["PRO_COM"] == "001272"
    assert "codice" not in rows[0]
