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
    The source CSV already has a column named 'codice' (value 'WRONG') AND a
    column 'PRO_COM' with the real numeric code.  The remap maps 'codice' <-
    'PRO_COM', so the remapped value must win over the pre-existing 'codice'.
    This verifies the merge order: r | remap, NOT remap | r.
    """
    conflict_fixture = Path("tests/fixtures/remap_codice_conflict.csv")
    spec = {
        "path": str(conflict_fixture),
        "delimiter": ";",
        "encoding": "utf-8",
        "columns": {
            "codice": "PRO_COM",  # PRO_COM="001272" must overwrite raw codice="WRONG"
        },
    }
    rows = _read_rows(spec, cache_dir=Path("/tmp"), offline=False)
    torino = next(r for r in rows if r["PRO_COM"] == "001272")
    assert torino["codice"] == "001272", "remap must overwrite pre-existing 'codice' column"
    assert torino["codice"] != "WRONG"


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


def test_remap_missing_source_column_raises_value_error():
    """A remap referencing a column absent from the CSV header must raise ValueError."""
    import pytest
    spec = {
        "path": str(FIXTURE),
        "delimiter": ";",
        "encoding": "utf-8",
        "columns": {
            "codice": "NONEXISTENT_COL",  # this column does not exist in remap_sample.csv
        },
    }
    with pytest.raises(ValueError, match="NONEXISTENT_COL"):
        _read_rows(spec, cache_dir=Path("/tmp"), offline=False)
