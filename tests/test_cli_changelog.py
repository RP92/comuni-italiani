# tests/test_cli_changelog.py
"""
Verifies that build() writes changelog entries when the dataset changes
between two successive runs.
"""
import json
import tomllib
from pathlib import Path

import pytest

from comuni_italiani.cli import build

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sources_toml(tmp_path: Path, anagrafica_path: Path) -> dict:
    """Return a config dict pointing at fixture CSVs, with anagrafica swapped."""
    fixture = Path("tests/fixtures")
    toml_text = f"""
[anagrafica]
path = "{anagrafica_path}"
delimiter = ";"
encoding = "utf-8"

[popolazione]
path = "{fixture / 'popolazione.csv'}"
delimiter = ";"
encoding = "utf-8"

[superficie]
path = "{fixture / 'superficie.csv'}"
delimiter = ";"
encoding = "utf-8"

[coordinate]
path = "{fixture / 'coordinate.csv'}"
delimiter = ";"
encoding = "utf-8"

[cap]
path = "{fixture / 'cap.csv'}"
delimiter = ";"
encoding = "utf-8"
"""
    return tomllib.loads(toml_text)


def _write_anagrafica(path: Path, rows: list[str]) -> None:
    """Write an ISTAT-format anagrafica CSV with a header + given data rows."""
    header = (
        "Codice Regione;Codice dell'Unità territoriale sovracomunale "
        "(valida a fini statistici);Denominazione dell'Unità territoriale "
        "sovracomunale (valida a fini statistici);Tipologia di Unità territoriale "
        "sovracomunale;Denominazione Regione;Codice Ripartizione Geografica;"
        "Ripartizione geografica;Flag Comune capoluogo di provincia/città "
        "metropolitana/libero consorzio;Sigla automobilistica;Codice Comune "
        "formato alfanumerico;Denominazione in italiano;Denominazione altra lingua;"
        "Codice Catastale del comune"
    )
    path.write_text("\n".join([header] + rows) + "\n", encoding="utf-8")


# Two anagrafica data rows using the same format as the fixture
_TORINO_ROW = "01;001;Torino;Città metropolitana;Piemonte;1;Nord-ovest;1;TO;001272;Torino;;L219"
_VERCELLI_ROW = "01;002;Vercelli;Provincia;Piemonte;1;Nord-ovest;1;VC;002158;Vercelli;;L750"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_changelog_created_on_first_run(tmp_path):
    """First run (no previous comuni.json) writes a changelog section."""
    ana = tmp_path / "anagrafica_v1.csv"
    _write_anagrafica(ana, [_TORINO_ROW, _VERCELLI_ROW])

    config = _make_sources_toml(tmp_path, ana)
    out_dir = tmp_path / "data"
    changelog = tmp_path / "CHANGELOG.md"

    build(config, cache_dir=tmp_path / "cache", out_dir=out_dir,
          offline=True, changelog_path=changelog)

    # Both comuni are "added" because there was no previous dataset
    assert changelog.exists()
    text = changelog.read_text(encoding="utf-8")
    assert "## [generated]" in text
    assert "Added: 2" in text


def test_changelog_updated_on_second_run_with_change(tmp_path):
    """
    Run build() twice: the second run adds one comune.
    The changelog file must contain a section mentioning the added count.
    """
    ana_v1 = tmp_path / "anagrafica_v1.csv"
    ana_v2 = tmp_path / "anagrafica_v2.csv"
    _write_anagrafica(ana_v1, [_TORINO_ROW])          # first run: 1 comune
    _write_anagrafica(ana_v2, [_TORINO_ROW, _VERCELLI_ROW])  # second run: 2 comuni

    out_dir = tmp_path / "data"
    changelog = tmp_path / "CHANGELOG.md"

    # First run
    config_v1 = _make_sources_toml(tmp_path, ana_v1)
    build(config_v1, cache_dir=tmp_path / "cache", out_dir=out_dir,
          offline=True, changelog_path=changelog)

    # Second run — adds Vercelli
    config_v2 = _make_sources_toml(tmp_path, ana_v2)
    build(config_v2, cache_dir=tmp_path / "cache", out_dir=out_dir,
          offline=True, changelog_path=changelog)

    text = changelog.read_text(encoding="utf-8")
    # Expect at least one section from the second run reporting 1 added comune
    assert "Added: 1" in text
    # The added codice must be listed (short list path)
    assert "002158" in text


def test_changelog_unchanged_when_no_diff(tmp_path):
    """
    If the dataset is identical between two runs the changelog must NOT grow.
    """
    ana = tmp_path / "anagrafica.csv"
    _write_anagrafica(ana, [_TORINO_ROW, _VERCELLI_ROW])

    out_dir = tmp_path / "data"
    changelog = tmp_path / "CHANGELOG.md"
    config = _make_sources_toml(tmp_path, ana)

    build(config, cache_dir=tmp_path / "cache", out_dir=out_dir,
          offline=True, changelog_path=changelog)
    size_after_first = changelog.stat().st_size

    # Second identical run — no changes
    build(config, cache_dir=tmp_path / "cache", out_dir=out_dir,
          offline=True, changelog_path=changelog)
    size_after_second = changelog.stat().st_size

    # File must not have grown
    assert size_after_second == size_after_first


def test_build_without_changelog_path_is_side_effect_free(tmp_path):
    """Passing changelog_path=None (the default) must not write any file."""
    ana = tmp_path / "anagrafica.csv"
    _write_anagrafica(ana, [_TORINO_ROW, _VERCELLI_ROW])

    config = _make_sources_toml(tmp_path, ana)
    out_dir = tmp_path / "data"
    changelog = tmp_path / "CHANGELOG.md"

    # No changelog_path passed
    build(config, cache_dir=tmp_path / "cache", out_dir=out_dir, offline=True)

    assert not changelog.exists(), "changelog must not be created without changelog_path"
