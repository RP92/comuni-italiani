# comuni-italiani Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public, auto-updating open dataset of all Italian comuni (2026), sourced from ISTAT + best-effort open CAP, distributed as JSON/CSV/NDJSON via CDN.

**Architecture:** A modular Python pipeline with decoupled stages — `download → parse → merge → emit → validate`. Each source is parsed into a normalized intermediate structure keyed by ISTAT `codice`; the anagrafica is the backbone that enrichment (popolazione, superficie, coordinate, CAP) joins onto. A GitHub Actions workflow reruns the pipeline monthly and opens a PR when `data/` changes.

**Tech Stack:** Python 3.11+, `pytest`, `jsonschema`, `requests`. Standard library `csv`/`json` for I/O. GitHub Actions for automation.

## Global Constraints

- Python **3.11+** (uses stdlib `tomllib`, modern typing).
- Dependencies limited to: `requests`, `jsonschema`, `pytest`. No pandas.
- **Schema stability:** every comune object has ALL schema keys present. Missing scalar → `null`; missing list → `[]`. Never omit a key.
- `codice` = ISTAT comune code as a zero-padded **string** (e.g. `"001272"`).
- `provincia.tipo` ∈ { `provincia`, `citta-metropolitana`, `libero-consorzio`, `provincia-autonoma` }.
- CAP confidence is **not** a per-comune field — it lives in an aggregate `data/quality-report.json`. The per-comune shape is exactly the spec §3 schema.
- All source files parsed as **UTF-8**, except ISTAT CSV which is **latin-1** (`cp1252`) with `;` delimiter.
- Commit after every task. Code + test committed together.
- Package import root: `comuni_italiani` (under `src/`).

---

## File Structure

```
comuni-italiani/
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── README.md
├── LICENSE                     # MIT (code)
├── LICENSE-DATA                # CC-BY 4.0 (data)
├── CHANGELOG.md
├── src/comuni_italiani/
│   ├── __init__.py
│   ├── slug.py                 # slugify() for regione filenames
│   ├── models.py               # TIPO_PROVINCIA map, normalization helpers
│   ├── parse/
│   │   ├── __init__.py
│   │   ├── anagrafica.py       # parse_anagrafica(rows) -> list[dict]
│   │   ├── popolazione.py      # parse_popolazione(rows) -> dict[str,int]
│   │   ├── superficie.py       # parse_superficie(rows) -> dict[str,float]
│   │   ├── coordinate.py       # parse_coordinate(rows) -> dict[str,dict]
│   │   └── cap.py              # parse_cap(rows) -> dict[str,list[str]]
│   ├── merge.py                # merge(...) -> list[dict]
│   ├── emit.py                 # emit(comuni, outdir)
│   ├── validate.py             # validate(comuni, schema_path) -> report
│   ├── download.py             # fetch(url, cache_path)
│   ├── changelog.py            # diff_datasets(old, new) -> dict
│   └── cli.py                  # main() orchestration
├── data/
│   ├── schema.json             # hand-written JSON Schema (contract)
│   └── (generated: comuni.json, comuni.csv, comuni.ndjson, regioni/*.json, quality-report.json)
├── tests/
│   ├── fixtures/               # trimmed real-format sample files
│   └── test_*.py
├── docs/superpowers/{specs,plans}/
└── .github/workflows/update.yml
```

Files that change together live together (each parser owns its own test + fixture). Split by responsibility (one source per parser), not by layer.

---

### Task 1: Project scaffolding & tooling

**Files:**
- Create: `pyproject.toml`, `requirements.txt`, `.gitignore`, `src/comuni_italiani/__init__.py`, `src/comuni_italiani/parse/__init__.py`, `tests/__init__.py`, `tests/test_smoke.py`

**Interfaces:**
- Consumes: nothing.
- Produces: importable package `comuni_italiani`; `pytest` runs green.

- [ ] **Step 1: Write `.gitignore`**

```gitignore
__pycache__/
*.pyc
.pytest_cache/
.cache/
*.egg-info/
.venv/
```

- [ ] **Step 2: Write `requirements.txt`**

```text
requests>=2.31
jsonschema>=4.21
pytest>=8.0
```

- [ ] **Step 3: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "comuni-italiani"
version = "0.1.0"
description = "Open dataset of Italian comuni, updated to 2026"
requires-python = ">=3.11"
dependencies = ["requests>=2.31", "jsonschema>=4.21"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 4: Create empty package files**

Create `src/comuni_italiani/__init__.py`, `src/comuni_italiani/parse/__init__.py`, `tests/__init__.py` (all empty).

- [ ] **Step 5: Write the smoke test**

```python
# tests/test_smoke.py
def test_package_imports():
    import comuni_italiani
    assert comuni_italiani is not None
```

- [ ] **Step 6: Run tests**

Run: `pip install -r requirements.txt && pytest -q`
Expected: PASS (1 test).

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml requirements.txt .gitignore src tests
git commit -m "chore: project scaffolding and pytest setup"
```

---

### Task 2: Slug utility

**Files:**
- Create: `src/comuni_italiani/slug.py`, `tests/test_slug.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `slugify(name: str) -> str` — lowercase ASCII hyphen-slug; for bilingual names with `/`, uses the part before the first `/`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_slug.py
import pytest
from comuni_italiani.slug import slugify

@pytest.mark.parametrize("name,expected", [
    ("Piemonte", "piemonte"),
    ("Emilia-Romagna", "emilia-romagna"),
    ("Friuli-Venezia Giulia", "friuli-venezia-giulia"),
    ("Valle d'Aosta/Vallée d'Aoste", "valle-d-aosta"),
    ("Trentino-Alto Adige/Südtirol", "trentino-alto-adige"),
])
def test_slugify(name, expected):
    assert slugify(name) == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_slug.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Write minimal implementation**

```python
# src/comuni_italiani/slug.py
import re
import unicodedata

def slugify(name: str) -> str:
    """Lowercase ASCII hyphen-slug. Bilingual 'IT/DE' -> part before '/'."""
    base = name.split("/", 1)[0]
    ascii_str = (
        unicodedata.normalize("NFKD", base)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    ascii_str = ascii_str.lower()
    ascii_str = re.sub(r"[^a-z0-9]+", "-", ascii_str)
    return ascii_str.strip("-")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_slug.py -v`
Expected: PASS (5 cases).

- [ ] **Step 5: Commit**

```bash
git add src/comuni_italiani/slug.py tests/test_slug.py
git commit -m "feat: slugify utility for regione filenames"
```

---

### Task 3: Domain constants (provincia tipo)

**Files:**
- Create: `src/comuni_italiani/models.py`, `tests/test_models.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `normalize_tipo(raw: str) -> str` mapping ISTAT "Tipologia di Unità territoriale sovracomunale" free text to the 4 canonical `provincia.tipo` values.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
import pytest
from comuni_italiani.models import normalize_tipo

@pytest.mark.parametrize("raw,expected", [
    ("Provincia", "provincia"),
    ("Città metropolitana", "citta-metropolitana"),
    ("Libero consorzio di comuni", "libero-consorzio"),
    ("Provincia autonoma", "provincia-autonoma"),
    ("  CITTA' METROPOLITANA ", "citta-metropolitana"),
])
def test_normalize_tipo(raw, expected):
    assert normalize_tipo(raw) == expected

def test_normalize_tipo_unknown_raises():
    with pytest.raises(ValueError):
        normalize_tipo("qualcosa")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Write minimal implementation**

```python
# src/comuni_italiani/models.py
import re
import unicodedata

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z]", "", s.lower())

_TIPO_RULES = [
    ("cittametropolitana", "citta-metropolitana"),
    ("liberoconsorzio", "libero-consorzio"),
    ("provinciaautonoma", "provincia-autonoma"),
    ("provincia", "provincia"),
]

def normalize_tipo(raw: str) -> str:
    key = _norm(raw)
    for needle, value in _TIPO_RULES:
        if needle in key:
            return value
    raise ValueError(f"Unknown provincia tipo: {raw!r}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/comuni_italiani/models.py tests/test_models.py
git commit -m "feat: normalize ISTAT provincia tipo to canonical values"
```

---

### Task 4: JSON Schema contract

**Files:**
- Create: `data/schema.json`, `tests/test_schema_file.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `data/schema.json` (JSON Schema draft 2020-12) describing an array of comune objects. Consumed by Task 12 (validate).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schema_file.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_schema_file.py -v`
Expected: FAIL (file not found).

- [ ] **Step 3: Write `data/schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "array",
  "items": {
    "type": "object",
    "additionalProperties": false,
    "required": ["nome","nomeAltraLingua","codice","codiceCatastale","sigla","cap","capoluogo","popolazione","superficie","coordinate","zona","regione","provincia"],
    "properties": {
      "nome": {"type": "string"},
      "nomeAltraLingua": {"type": ["string","null"]},
      "codice": {"type": "string", "pattern": "^[0-9]{6}$"},
      "codiceCatastale": {"type": ["string","null"], "pattern": "^[A-Z][0-9]{3}$"},
      "sigla": {"type": ["string","null"], "pattern": "^[A-Z]{1,2}$"},
      "cap": {"type": "array", "items": {"type": "string", "pattern": "^[0-9]{5}$"}},
      "capoluogo": {"type": "boolean"},
      "popolazione": {"type": ["integer","null"], "minimum": 0},
      "superficie": {"type": ["number","null"], "minimum": 0},
      "coordinate": {
        "type": ["object","null"],
        "additionalProperties": false,
        "required": ["lat","lng"],
        "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}
      },
      "zona": {
        "type": "object", "additionalProperties": false,
        "required": ["nome","codice"],
        "properties": {"nome": {"type": "string"}, "codice": {"type": "string"}}
      },
      "regione": {
        "type": "object", "additionalProperties": false,
        "required": ["nome","codice"],
        "properties": {"nome": {"type": "string"}, "codice": {"type": "string"}}
      },
      "provincia": {
        "type": "object", "additionalProperties": false,
        "required": ["nome","codice","sigla","tipo"],
        "properties": {
          "nome": {"type": "string"},
          "codice": {"type": "string"},
          "sigla": {"type": ["string","null"]},
          "tipo": {"enum": ["provincia","citta-metropolitana","libero-consorzio","provincia-autonoma"]}
        }
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_schema_file.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add data/schema.json tests/test_schema_file.py
git commit -m "feat: JSON Schema contract for comune objects"
```

---

### Task 5: Parse ISTAT anagrafica

**Files:**
- Create: `src/comuni_italiani/parse/anagrafica.py`, `tests/fixtures/istat_anagrafica.csv`, `tests/test_parse_anagrafica.py`

**Interfaces:**
- Consumes: `normalize_tipo` (Task 3).
- Produces: `parse_anagrafica(rows: Iterable[dict]) -> list[dict]` where each dict has keys: `nome, nomeAltraLingua, codice, codiceCatastale, sigla, capoluogo, zona{nome,codice}, regione{nome,codice}, provincia{nome,codice,sigla,tipo}`. `rows` are `csv.DictReader` rows using the ISTAT header names below.

**ISTAT column headers used** (exact strings, from the ISTAT "Elenco comuni italiani" CSV):
- `Codice Comune formato alfanumerico` → `codice`
- `Denominazione in italiano` → `nome`
- `Denominazione altra lingua` → `nomeAltraLingua` (empty → `None`)
- `Codice Catastale del comune` → `codiceCatastale`
- `Sigla automobilistica` → `sigla` / `provincia.sigla`
- `Flag Comune capoluogo di provincia/città metropolitana/libero consorzio` → `capoluogo` (`"1"`→True)
- `Ripartizione geografica` + `Codice Ripartizione Geografica` → `zona`
- `Denominazione Regione` + `Codice Regione` → `regione`
- `Denominazione dell'Unità territoriale sovracomunale (valida a fini statistici)` + `Codice dell'Unità territoriale sovracomunale (valida ai fini statistici)` → `provincia.nome`/`provincia.codice`
- `Tipologia di Unità territoriale sovracomunale` → `provincia.tipo` (via `normalize_tipo`)

- [ ] **Step 1: Write the fixture**

`tests/fixtures/istat_anagrafica.csv` (semicolon-delimited; 2 data rows — header trimmed to the columns the parser reads):

```csv
Codice Regione;Codice dell'Unità territoriale sovracomunale (valida ai fini statistici);Denominazione dell'Unità territoriale sovracomunale (valida a fini statistici);Tipologia di Unità territoriale sovracomunale;Denominazione Regione;Codice Ripartizione Geografica;Ripartizione geografica;Flag Comune capoluogo di provincia/città metropolitana/libero consorzio;Sigla automobilistica;Codice Comune formato alfanumerico;Denominazione in italiano;Denominazione altra lingua;Codice Catastale del comune
01;001;Torino;Città metropolitana;Piemonte;1;Nord-ovest;1;TO;001272;Torino;;L219
01;002;Vercelli;Provincia;Piemonte;1;Nord-ovest;1;VC;002158;Vercelli;;L750
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_parse_anagrafica.py
import csv
from pathlib import Path
from comuni_italiani.parse.anagrafica import parse_anagrafica

def _rows():
    text = Path("tests/fixtures/istat_anagrafica.csv").read_text(encoding="utf-8")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))

def test_parses_torino():
    out = {c["codice"]: c for c in parse_anagrafica(_rows())}
    t = out["001272"]
    assert t["nome"] == "Torino"
    assert t["nomeAltraLingua"] is None
    assert t["codiceCatastale"] == "L219"
    assert t["sigla"] == "TO"
    assert t["capoluogo"] is True
    assert t["zona"] == {"nome": "Nord-ovest", "codice": "1"}
    assert t["regione"] == {"nome": "Piemonte", "codice": "01"}
    assert t["provincia"] == {"nome": "Torino", "codice": "001", "sigla": "TO", "tipo": "citta-metropolitana"}

def test_row_count():
    assert len(parse_anagrafica(_rows())) == 2
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_parse_anagrafica.py -v`
Expected: FAIL (module not found).

- [ ] **Step 4: Write minimal implementation**

```python
# src/comuni_italiani/parse/anagrafica.py
from typing import Iterable
from comuni_italiani.models import normalize_tipo

C_CODICE = "Codice Comune formato alfanumerico"
C_NOME = "Denominazione in italiano"
C_ALTRA = "Denominazione altra lingua"
C_CATAST = "Codice Catastale del comune"
C_SIGLA = "Sigla automobilistica"
C_CAP_FLAG = "Flag Comune capoluogo di provincia/città metropolitana/libero consorzio"
C_ZONA = "Ripartizione geografica"
C_ZONA_COD = "Codice Ripartizione Geografica"
C_REG = "Denominazione Regione"
C_REG_COD = "Codice Regione"
C_PROV = "Denominazione dell'Unità territoriale sovracomunale (valida a fini statistici)"
C_PROV_COD = "Codice dell'Unità territoriale sovracomunale (valida ai fini statistici)"
C_PROV_TIPO = "Tipologia di Unità territoriale sovracomunale"

def parse_anagrafica(rows: Iterable[dict]) -> list[dict]:
    out = []
    for r in rows:
        altra = (r.get(C_ALTRA) or "").strip()
        out.append({
            "codice": r[C_CODICE].strip(),
            "nome": r[C_NOME].strip(),
            "nomeAltraLingua": altra or None,
            "codiceCatastale": (r.get(C_CATAST) or "").strip() or None,
            "sigla": (r.get(C_SIGLA) or "").strip() or None,
            "capoluogo": (r.get(C_CAP_FLAG) or "").strip() == "1",
            "zona": {"nome": r[C_ZONA].strip(), "codice": r[C_ZONA_COD].strip()},
            "regione": {"nome": r[C_REG].strip(), "codice": r[C_REG_COD].strip()},
            "provincia": {
                "nome": r[C_PROV].strip(),
                "codice": r[C_PROV_COD].strip(),
                "sigla": (r.get(C_SIGLA) or "").strip() or None,
                "tipo": normalize_tipo(r[C_PROV_TIPO]),
            },
        })
    return out
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_parse_anagrafica.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/comuni_italiani/parse/anagrafica.py tests/fixtures/istat_anagrafica.csv tests/test_parse_anagrafica.py
git commit -m "feat: parse ISTAT anagrafica into normalized comune records"
```

---

### Task 6: Parse popolazione

**Files:**
- Create: `src/comuni_italiani/parse/popolazione.py`, `tests/fixtures/popolazione.csv`, `tests/test_parse_popolazione.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse_popolazione(rows: Iterable[dict]) -> dict[str,int]` mapping `codice` → resident population. Columns: `codice`, `popolazione`.

- [ ] **Step 1: Write the fixture**

`tests/fixtures/popolazione.csv`:

```csv
codice;popolazione
001272;848196
002158;46552
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_parse_popolazione.py
import csv
from pathlib import Path
from comuni_italiani.parse.popolazione import parse_popolazione

def _rows():
    text = Path("tests/fixtures/popolazione.csv").read_text(encoding="utf-8")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))

def test_parse_popolazione():
    out = parse_popolazione(_rows())
    assert out == {"001272": 848196, "002158": 46552}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_parse_popolazione.py -v`
Expected: FAIL.

- [ ] **Step 4: Write minimal implementation**

```python
# src/comuni_italiani/parse/popolazione.py
from typing import Iterable

def parse_popolazione(rows: Iterable[dict]) -> dict[str, int]:
    out = {}
    for r in rows:
        codice = r["codice"].strip()
        raw = (r.get("popolazione") or "").strip().replace(".", "")
        if raw:
            out[codice] = int(raw)
    return out
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_parse_popolazione.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/comuni_italiani/parse/popolazione.py tests/fixtures/popolazione.csv tests/test_parse_popolazione.py
git commit -m "feat: parse ISTAT resident population"
```

> **Implementer note (source mapping):** the real ISTAT population file uses different
> column names. The `download`/`cli` stage (Task 13/14) is responsible for pre-mapping
> the raw ISTAT columns to `codice`/`popolazione` before calling this parser, OR you
> adjust the two column constants here to match the chosen ISTAT file. Keep the fixture
> representative of the shape you actually feed in.

---

### Task 7: Parse superficie

**Files:**
- Create: `src/comuni_italiani/parse/superficie.py`, `tests/fixtures/superficie.csv`, `tests/test_parse_superficie.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse_superficie(rows: Iterable[dict]) -> dict[str,float]` mapping `codice` → km² (float). Columns: `codice`, `superficie` (Italian decimal comma tolerated).

- [ ] **Step 1: Write the fixture**

`tests/fixtures/superficie.csv`:

```csv
codice;superficie
001272;130,06
002158;79,78
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_parse_superficie.py
import csv
from pathlib import Path
from comuni_italiani.parse.superficie import parse_superficie

def _rows():
    text = Path("tests/fixtures/superficie.csv").read_text(encoding="utf-8")
    return list(csv.DictReader(text.splitlines(), delimiter=";"))

def test_parse_superficie():
    out = parse_superficie(_rows())
    assert out == {"001272": 130.06, "002158": 79.78}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_parse_superficie.py -v`
Expected: FAIL.

- [ ] **Step 4: Write minimal implementation**

```python
# src/comuni_italiani/parse/superficie.py
from typing import Iterable

def parse_superficie(rows: Iterable[dict]) -> dict[str, float]:
    out = {}
    for r in rows:
        codice = r["codice"].strip()
        raw = (r.get("superficie") or "").strip().replace(".", "").replace(",", ".")
        if raw:
            out[codice] = float(raw)
    return out
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_parse_superficie.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/comuni_italiani/parse/superficie.py tests/fixtures/superficie.csv tests/test_parse_superficie.py
git commit -m "feat: parse ISTAT comune surface area"
```

---

### Task 8: Parse coordinate

**Files:**
- Create: `src/comuni_italiani/parse/coordinate.py`, `tests/fixtures/coordinate.csv`, `tests/test_parse_coordinate.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse_coordinate(rows: Iterable[dict]) -> dict[str, dict]` mapping `codice` → `{"lat": float, "lng": float}`. Columns: `codice`, `lat`, `lng`. Rows with missing/blank lat or lng are skipped.

- [ ] **Step 1: Write the fixture**

`tests/fixtures/coordinate.csv`:

```csv
codice;lat;lng
001272;45.0703;7.6869
002158;45.3200;8.4194
003999;;
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_parse_coordinate.py
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_parse_coordinate.py -v`
Expected: FAIL.

- [ ] **Step 4: Write minimal implementation**

```python
# src/comuni_italiani/parse/coordinate.py
from typing import Iterable

def parse_coordinate(rows: Iterable[dict]) -> dict[str, dict]:
    out = {}
    for r in rows:
        codice = r["codice"].strip()
        lat = (r.get("lat") or "").strip()
        lng = (r.get("lng") or "").strip()
        if lat and lng:
            out[codice] = {"lat": float(lat), "lng": float(lng)}
    return out
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_parse_coordinate.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/comuni_italiani/parse/coordinate.py tests/fixtures/coordinate.csv tests/test_parse_coordinate.py
git commit -m "feat: parse comune coordinates"
```

---

### Task 9: CAP source spike + parser

**Files:**
- Create: `src/comuni_italiani/parse/cap.py`, `tests/fixtures/cap.csv`, `tests/test_parse_cap.py`, `docs/superpowers/specs/2026-08-09-cap-source-decision.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse_cap(rows: Iterable[dict]) -> dict[str, list[str]]` mapping `codice` → **sorted, deduplicated** list of 5-digit CAP strings. Columns: `codice`, `cap`. A single source row may carry one CAP; multiple rows per `codice` accumulate.

- [ ] **Step 1 (SPIKE — do this first): Choose the CAP source and document it**

Research and pick the best open CAP source available in 2026. Candidate starting points to evaluate (verify license, coverage %, freshness, and that it keys by ISTAT `codice` or by a joinable name+provincia):
- OpenStreetMap `addr:postcode` / boundary `postal_code` aggregated per comune.
- Community CSV datasets pairing ISTAT code ↔ CAP (search GitHub for "comuni cap istat csv"; assess license + last-update).
- Any dataset that also carries lat/lng (could double as the coordinate source in Task 8).

Write `docs/superpowers/specs/2026-08-09-cap-source-decision.md` recording: chosen source, URL, license, join key, measured coverage (% comuni with ≥1 CAP), and known gaps. **Do not proceed to the parser until this file exists.** If the chosen source keys differently (e.g. by name), the pre-mapping to `codice` happens in the `cli`/`download` stage before this parser is called — this parser always receives `codice`+`cap` rows.

- [ ] **Step 2: Write the fixture**

`tests/fixtures/cap.csv`:

```csv
codice;cap
001272;10121
001272;10122
001272;10121
002158;13100
```

- [ ] **Step 3: Write the failing test**

```python
# tests/test_parse_cap.py
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
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/test_parse_cap.py -v`
Expected: FAIL.

- [ ] **Step 5: Write minimal implementation**

```python
# src/comuni_italiani/parse/cap.py
import re
from typing import Iterable

_CAP_RE = re.compile(r"^\d{5}$")

def parse_cap(rows: Iterable[dict]) -> dict[str, list[str]]:
    acc: dict[str, set] = {}
    for r in rows:
        codice = r["codice"].strip()
        cap = (r.get("cap") or "").strip()
        if _CAP_RE.match(cap):
            acc.setdefault(codice, set()).add(cap)
    return {k: sorted(v) for k, v in acc.items()}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_parse_cap.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/comuni_italiani/parse/cap.py tests/fixtures/cap.csv tests/test_parse_cap.py docs/superpowers/specs/2026-08-09-cap-source-decision.md
git commit -m "feat: parse CAP source into per-comune lists + source decision doc"
```

---

### Task 10: Merge stage

**Files:**
- Create: `src/comuni_italiani/merge.py`, `tests/test_merge.py`

**Interfaces:**
- Consumes: anagrafica records (Task 5) + the four enrichment dicts (Tasks 6–9).
- Produces: `merge(anagrafica: list[dict], popolazione: dict, superficie: dict, coordinate: dict, cap: dict) -> list[dict]` — final comune objects matching `data/schema.json`, sorted by `codice`. Missing enrichment → `null`/`[]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_merge.py
from comuni_italiani.merge import merge

ANAG = [{
    "codice": "001272", "nome": "Torino", "nomeAltraLingua": None,
    "codiceCatastale": "L219", "sigla": "TO", "capoluogo": True,
    "zona": {"nome": "Nord-ovest", "codice": "1"},
    "regione": {"nome": "Piemonte", "codice": "01"},
    "provincia": {"nome": "Torino", "codice": "001", "sigla": "TO", "tipo": "citta-metropolitana"},
}]

def test_merge_full():
    out = merge(ANAG, {"001272": 848196}, {"001272": 130.06},
                {"001272": {"lat": 45.07, "lng": 7.68}}, {"001272": ["10121"]})
    c = out[0]
    assert c["popolazione"] == 848196
    assert c["superficie"] == 130.06
    assert c["coordinate"] == {"lat": 45.07, "lng": 7.68}
    assert c["cap"] == ["10121"]

def test_merge_missing_enrichment_is_null():
    out = merge(ANAG, {}, {}, {}, {})
    c = out[0]
    assert c["popolazione"] is None
    assert c["superficie"] is None
    assert c["coordinate"] is None
    assert c["cap"] == []
    assert set(c.keys()) == {
        "nome","nomeAltraLingua","codice","codiceCatastale","sigla","cap",
        "capoluogo","popolazione","superficie","coordinate","zona","regione","provincia",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_merge.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# src/comuni_italiani/merge.py
def merge(anagrafica, popolazione, superficie, coordinate, cap):
    out = []
    for a in anagrafica:
        codice = a["codice"]
        out.append({
            "nome": a["nome"],
            "nomeAltraLingua": a["nomeAltraLingua"],
            "codice": codice,
            "codiceCatastale": a["codiceCatastale"],
            "sigla": a["sigla"],
            "cap": cap.get(codice, []),
            "capoluogo": a["capoluogo"],
            "popolazione": popolazione.get(codice),
            "superficie": superficie.get(codice),
            "coordinate": coordinate.get(codice),
            "zona": a["zona"],
            "regione": a["regione"],
            "provincia": a["provincia"],
        })
    out.sort(key=lambda c: c["codice"])
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_merge.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/comuni_italiani/merge.py tests/test_merge.py
git commit -m "feat: merge anagrafica backbone with enrichment sources"
```

---

### Task 11: Emit stage (JSON/CSV/NDJSON + per-regione split)

**Files:**
- Create: `src/comuni_italiani/emit.py`, `tests/test_emit.py`

**Interfaces:**
- Consumes: final comuni list (Task 10), `slugify` (Task 2).
- Produces: `emit(comuni: list[dict], outdir: Path) -> None` writing `comuni.json`, `comuni.csv`, `comuni.ndjson`, and `regioni/<slug>.json`. JSON uses `ensure_ascii=False`, 2-space indent, trailing newline. CSV flattens nested fields with dotted headers and joins `cap` with `,`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_emit.py
import json
from pathlib import Path
from comuni_italiani.emit import emit

COMUNI = [{
    "nome": "Torino", "nomeAltraLingua": None, "codice": "001272",
    "codiceCatastale": "L219", "sigla": "TO", "cap": ["10121","10122"],
    "capoluogo": True, "popolazione": 848196, "superficie": 130.06,
    "coordinate": {"lat": 45.07, "lng": 7.68},
    "zona": {"nome": "Nord-ovest", "codice": "1"},
    "regione": {"nome": "Piemonte", "codice": "01"},
    "provincia": {"nome": "Torino", "codice": "001", "sigla": "TO", "tipo": "citta-metropolitana"},
}]

def test_emit_writes_all_formats(tmp_path):
    emit(COMUNI, tmp_path)
    data = json.loads((tmp_path / "comuni.json").read_text(encoding="utf-8"))
    assert data == COMUNI
    assert (tmp_path / "comuni.csv").exists()
    nd = (tmp_path / "comuni.ndjson").read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(nd[0])["codice"] == "001272"
    reg = json.loads((tmp_path / "regioni" / "piemonte.json").read_text(encoding="utf-8"))
    assert reg[0]["nome"] == "Torino"

def test_emit_csv_flattens_cap(tmp_path):
    emit(COMUNI, tmp_path)
    csv_text = (tmp_path / "comuni.csv").read_text(encoding="utf-8")
    assert '"10121,10122"' in csv_text or "10121,10122" in csv_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_emit.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# src/comuni_italiani/emit.py
import csv
import io
import json
from pathlib import Path
from comuni_italiani.slug import slugify

CSV_COLUMNS = [
    "codice", "nome", "nomeAltraLingua", "codiceCatastale", "sigla",
    "cap", "capoluogo", "popolazione", "superficie",
    "coordinate.lat", "coordinate.lng",
    "zona.nome", "zona.codice", "regione.nome", "regione.codice",
    "provincia.nome", "provincia.codice", "provincia.sigla", "provincia.tipo",
]

def _flat(c: dict) -> dict:
    coord = c["coordinate"] or {}
    return {
        "codice": c["codice"], "nome": c["nome"],
        "nomeAltraLingua": c["nomeAltraLingua"] or "",
        "codiceCatastale": c["codiceCatastale"] or "",
        "sigla": c["sigla"] or "",
        "cap": ",".join(c["cap"]),
        "capoluogo": "1" if c["capoluogo"] else "0",
        "popolazione": c["popolazione"] if c["popolazione"] is not None else "",
        "superficie": c["superficie"] if c["superficie"] is not None else "",
        "coordinate.lat": coord.get("lat", ""),
        "coordinate.lng": coord.get("lng", ""),
        "zona.nome": c["zona"]["nome"], "zona.codice": c["zona"]["codice"],
        "regione.nome": c["regione"]["nome"], "regione.codice": c["regione"]["codice"],
        "provincia.nome": c["provincia"]["nome"], "provincia.codice": c["provincia"]["codice"],
        "provincia.sigla": c["provincia"]["sigla"] or "",
        "provincia.tipo": c["provincia"]["tipo"],
    }

def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def emit(comuni: list[dict], outdir: Path) -> None:
    outdir = Path(outdir)
    (outdir / "regioni").mkdir(parents=True, exist_ok=True)
    _write_json(outdir / "comuni.json", comuni)

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS)
    w.writeheader()
    for c in comuni:
        w.writerow(_flat(c))
    (outdir / "comuni.csv").write_text(buf.getvalue(), encoding="utf-8")

    with (outdir / "comuni.ndjson").open("w", encoding="utf-8") as f:
        for c in comuni:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    by_reg: dict[str, list] = {}
    for c in comuni:
        by_reg.setdefault(slugify(c["regione"]["nome"]), []).append(c)
    for slug, items in by_reg.items():
        _write_json(outdir / "regioni" / f"{slug}.json", items)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_emit.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/comuni_italiani/emit.py tests/test_emit.py
git commit -m "feat: emit JSON/CSV/NDJSON + per-regione split files"
```

---

### Task 12: Validate stage

**Files:**
- Create: `src/comuni_italiani/validate.py`, `tests/test_validate.py`

**Interfaces:**
- Consumes: final comuni list (Task 10), `data/schema.json` (Task 4).
- Produces: `validate(comuni: list[dict], schema_path: Path, min_count=7000, max_count=8200) -> dict` returning a report `{"count", "cap_coverage", "errors": [...]}`. Raises `ValueError` if hard invariants fail (schema violation, duplicate codice, count out of range).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_validate.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validate.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# src/comuni_italiani/validate.py
import json
from pathlib import Path
from jsonschema import Draft202012Validator

def validate(comuni, schema_path, min_count=7000, max_count=8200):
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(comuni)

    count = len(comuni)
    if not (min_count <= count <= max_count):
        raise ValueError(f"comuni count {count} out of range [{min_count},{max_count}]")

    codici = [c["codice"] for c in comuni]
    dupes = {x for x in codici if codici.count(x) > 1}
    if dupes:
        raise ValueError(f"duplicate codice: {sorted(dupes)[:5]}")

    with_cap = sum(1 for c in comuni if c["cap"])
    return {
        "count": count,
        "cap_coverage": round(with_cap / count, 4) if count else 0.0,
        "errors": [],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validate.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/comuni_italiani/validate.py tests/test_validate.py
git commit -m "feat: validate dataset against schema + invariants"
```

---

### Task 13: Download stage (fetch + cache)

**Files:**
- Create: `src/comuni_italiani/download.py`, `tests/test_download.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `fetch(url: str, cache_path: Path, *, session=None, force=False) -> Path` — downloads `url` to `cache_path` unless it already exists (unless `force`). Returns the path. `session` defaults to a `requests.Session()`; tests inject a fake.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_download.py
from pathlib import Path
from comuni_italiani.download import fetch

class FakeResp:
    def __init__(self, content): self.content = content
    def raise_for_status(self): pass

class FakeSession:
    def __init__(self): self.calls = 0
    def get(self, url, timeout=0):
        self.calls += 1
        return FakeResp(b"hello")

def test_fetch_writes_and_caches(tmp_path):
    s = FakeSession()
    dest = tmp_path / "f.bin"
    p1 = fetch("http://x", dest, session=s)
    assert p1.read_bytes() == b"hello"
    # second call uses cache, no new request
    fetch("http://x", dest, session=s)
    assert s.calls == 1

def test_fetch_force_refetches(tmp_path):
    s = FakeSession()
    dest = tmp_path / "f.bin"
    fetch("http://x", dest, session=s)
    fetch("http://x", dest, session=s, force=True)
    assert s.calls == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_download.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# src/comuni_italiani/download.py
from pathlib import Path
import requests

def fetch(url, cache_path, *, session=None, force=False):
    cache_path = Path(cache_path)
    if cache_path.exists() and not force:
        return cache_path
    session = session or requests.Session()
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(resp.content)
    return cache_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_download.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/comuni_italiani/download.py tests/test_download.py
git commit -m "feat: cached HTTP fetch for source files"
```

---

### Task 14: CLI orchestrator

**Files:**
- Create: `src/comuni_italiani/cli.py`, `tests/fixtures/sources.toml`, `tests/test_cli_integration.py`

**Interfaces:**
- Consumes: all parse/merge/emit/validate/download modules.
- Produces: `build(config: dict, cache_dir: Path, out_dir: Path, *, offline=False) -> dict` — runs the full pipeline over the configured sources and returns the validation report. Also a `main(argv=None)` entrypoint reading `sources.toml`.

**Source config shape** (`sources.toml`): each source has `url` and, where the raw columns differ from the parser's expected `codice`/value headers, a `columns` remap table. The orchestrator applies the remap after reading each CSV, before calling the parser. This is where real ISTAT/CAP column names are wired without touching parser code.

- [ ] **Step 1: Write the integration fixture config**

`tests/fixtures/sources.toml` (points at the local fixture CSVs; anagrafica needs no remap, the others already use `codice`):

```toml
[anagrafica]
path = "tests/fixtures/istat_anagrafica.csv"
delimiter = ";"
encoding = "utf-8"

[popolazione]
path = "tests/fixtures/popolazione.csv"
delimiter = ";"
encoding = "utf-8"

[superficie]
path = "tests/fixtures/superficie.csv"
delimiter = ";"
encoding = "utf-8"

[coordinate]
path = "tests/fixtures/coordinate.csv"
delimiter = ";"
encoding = "utf-8"

[cap]
path = "tests/fixtures/cap.csv"
delimiter = ";"
encoding = "utf-8"
```

- [ ] **Step 2: Write the failing integration test**

```python
# tests/test_cli_integration.py
import json
import tomllib
from pathlib import Path
from comuni_italiani.cli import build

def test_build_end_to_end(tmp_path):
    config = tomllib.loads(Path("tests/fixtures/sources.toml").read_text(encoding="utf-8"))
    out = tmp_path / "data"
    report = build(config, cache_dir=tmp_path / "cache", out_dir=out, offline=True)
    assert report["count"] == 2
    data = json.loads((out / "comuni.json").read_text(encoding="utf-8"))
    torino = next(c for c in data if c["codice"] == "001272")
    assert torino["popolazione"] == 848196
    assert torino["superficie"] == 130.06
    assert torino["cap"] == ["10121", "10122"]
    assert torino["coordinate"] == {"lat": 45.0703, "lng": 7.6869}
    assert (out / "regioni" / "piemonte.json").exists()
    assert (out / "quality-report.json").exists()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_cli_integration.py -v`
Expected: FAIL.

- [ ] **Step 4: Write minimal implementation**

```python
# src/comuni_italiani/cli.py
import csv
import json
import sys
import tomllib
from pathlib import Path

from comuni_italiani.download import fetch
from comuni_italiani.parse.anagrafica import parse_anagrafica
from comuni_italiani.parse.popolazione import parse_popolazione
from comuni_italiani.parse.superficie import parse_superficie
from comuni_italiani.parse.coordinate import parse_coordinate
from comuni_italiani.parse.cap import parse_cap
from comuni_italiani.merge import merge
from comuni_italiani.emit import emit
from comuni_italiani.validate import validate

SCHEMA_PATH = Path("data/schema.json")

def _read_rows(spec: dict, cache_dir: Path, offline: bool) -> list[dict]:
    if "path" in spec:
        path = Path(spec["path"])
    else:
        cache_dir.mkdir(parents=True, exist_ok=True)
        path = fetch(spec["url"], cache_dir / spec["cache"], force=False) if not offline else Path(spec["cache"])
    text = path.read_text(encoding=spec.get("encoding", "utf-8"))
    rows = list(csv.DictReader(text.splitlines(), delimiter=spec.get("delimiter", ";")))
    remap = spec.get("columns")
    if remap:
        rows = [{new: r.get(old, "") for new, old in remap.items()} | r for r in rows]
    return rows

def build(config: dict, cache_dir: Path, out_dir: Path, *, offline: bool = False) -> dict:
    cache_dir, out_dir = Path(cache_dir), Path(out_dir)
    anagrafica = parse_anagrafica(_read_rows(config["anagrafica"], cache_dir, offline))
    popolazione = parse_popolazione(_read_rows(config["popolazione"], cache_dir, offline))
    superficie = parse_superficie(_read_rows(config["superficie"], cache_dir, offline))
    coordinate = parse_coordinate(_read_rows(config["coordinate"], cache_dir, offline))
    cap = parse_cap(_read_rows(config["cap"], cache_dir, offline))

    comuni = merge(anagrafica, popolazione, superficie, coordinate, cap)
    emit(comuni, out_dir)
    report = validate(comuni, SCHEMA_PATH, min_count=len(comuni), max_count=len(comuni)) \
        if offline else validate(comuni, SCHEMA_PATH)
    (out_dir / "quality-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report

def main(argv=None):
    argv = argv or sys.argv[1:]
    config_path = Path(argv[0]) if argv else Path("sources.toml")
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    report = build(config, cache_dir=Path(".cache"), out_dir=Path("data"))
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_cli_integration.py -v`
Expected: PASS.

- [ ] **Step 6: Run the full suite**

Run: `pytest -q`
Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/comuni_italiani/cli.py tests/fixtures/sources.toml tests/test_cli_integration.py
git commit -m "feat: CLI orchestrator running the full pipeline"
```

---

### Task 15: Changelog diff generator

**Files:**
- Create: `src/comuni_italiani/changelog.py`, `tests/test_changelog.py`

**Interfaces:**
- Consumes: two comuni lists (old, new).
- Produces: `diff_datasets(old: list[dict], new: list[dict]) -> dict` returning `{"added": [codici], "removed": [codici], "modified": [codici]}`, each sorted. `modified` = same codice, any field differs.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_changelog.py
from comuni_italiani.changelog import diff_datasets

def _c(codice, nome="X"):
    return {"codice": codice, "nome": nome}

def test_diff_added_removed_modified():
    old = [_c("001"), _c("002"), _c("003", "Vecchio")]
    new = [_c("002"), _c("003", "Nuovo"), _c("004")]
    d = diff_datasets(old, new)
    assert d["added"] == ["004"]
    assert d["removed"] == ["001"]
    assert d["modified"] == ["003"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_changelog.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# src/comuni_italiani/changelog.py
def diff_datasets(old, new):
    old_by = {c["codice"]: c for c in old}
    new_by = {c["codice"]: c for c in new}
    old_ids, new_ids = set(old_by), set(new_by)
    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)
    modified = sorted(
        cid for cid in old_ids & new_ids if old_by[cid] != new_by[cid]
    )
    return {"added": added, "removed": removed, "modified": modified}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_changelog.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/comuni_italiani/changelog.py tests/test_changelog.py
git commit -m "feat: dataset diff generator for changelog"
```

---

### Task 16: Docs, licenses, and GitHub Actions workflow

**Files:**
- Create: `README.md`, `LICENSE`, `LICENSE-DATA`, `CHANGELOG.md`, `.github/workflows/update.yml`, `sources.toml`

**Interfaces:**
- Consumes: `cli.main` (Task 14).
- Produces: public-facing docs + the monthly automation. No new Python API.

- [ ] **Step 1: Write `LICENSE` (MIT)**

Standard MIT text, holder "Raffaele Pappalardo", year 2026.

- [ ] **Step 2: Write `LICENSE-DATA`**

Full text of **Creative Commons Attribution 4.0 International (CC-BY 4.0)**. Add a header line: "The datasets in `data/` are licensed CC-BY 4.0. Attribution: ISTAT and the CAP/coordinate sources documented in the README."

- [ ] **Step 3: Write `CHANGELOG.md`**

```markdown
# Changelog

All notable dataset changes are recorded here. Format: added / removed / modified
comuni per generation run.

## [Unreleased]
- Initial dataset.
```

- [ ] **Step 4: Write `README.md`**

Must cover: what it is (comuni italiani 2026, ISTAT-based), schema table (all 13 fields with type + description), **CDN usage** with a concrete URL (`https://cdn.jsdelivr.net/gh/RP92/comuni-italiani/data/comuni.json`), available formats (JSON/CSV/NDJSON/per-regione), the CAP best-effort disclaimer + link to `docs/superpowers/specs/2026-08-09-cap-source-decision.md`, how to rebuild locally (`pip install -r requirements.txt && python -m comuni_italiani.cli sources.toml`), licensing (MIT code / CC-BY 4.0 data), and credit to `matteocontrini/comuni-json` as inspiration.

- [ ] **Step 5: Write `sources.toml`** (production config)

Real source URLs + column remaps for ISTAT population/superficie and the chosen CAP/coordinate sources (from Task 9 spike). Each non-anagrafica source uses `url`, `cache`, and a `columns` remap to `codice`/value. Mirror the shape of `tests/fixtures/sources.toml` but with `url`/`cache` instead of `path`.

- [ ] **Step 6: Write `.github/workflows/update.yml`**

```yaml
name: update-dataset
on:
  schedule:
    - cron: "0 4 1 * *"   # monthly, 1st at 04:00 UTC
  workflow_dispatch:
jobs:
  rebuild:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python -m comuni_italiani.cli sources.toml
      - name: Open PR on changes
        uses: peter-evans/create-pull-request@v6
        with:
          branch: auto/dataset-update
          title: "chore: dataset update"
          commit-message: "chore: automated dataset regeneration"
          body: "Automated monthly regeneration. Review the diff in `data/` before merging."
          add-paths: |
            data/**
            CHANGELOG.md
```

- [ ] **Step 7: Verify the workflow file is valid YAML**

Run: `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/update.yml'))"`
(If PyYAML isn't installed: `pip install pyyaml` first. This is a local check only, not a runtime dep.)
Expected: no error.

- [ ] **Step 8: Run the full test suite one final time**

Run: `pytest -q`
Expected: all PASS.

- [ ] **Step 9: Commit**

```bash
git add README.md LICENSE LICENSE-DATA CHANGELOG.md .github/workflows/update.yml sources.toml
git commit -m "docs: README, licenses, and monthly auto-update workflow"
```

---

## Self-Review

**1. Spec coverage:**
- §1 objective / scope → Tasks 1, 16 (README states scope). ✓
- §2 sources (ISTAT anagrafica/pop/superficie/coord, CAP best-effort) → Tasks 5–9. ✓
- §2 CAP flag di confidenza → realized as aggregate `quality-report.json` (Task 12/14) + Global Constraints note. ✓
- §3 revised schema (all fields, null-stable) → Task 4 (schema.json), Task 10 (merge builds exact shape), Task 10 test asserts key set. ✓
- §4 repo structure + multiple formats + per-regione split → Task 11, Task 16. ✓
- §4 CDN distribution → Task 16 README. ✓
- §5 pipeline stages download→parse→merge→emit→validate → Tasks 5–14. ✓
- §5 GitHub Actions monthly + PR + CHANGELOG diff → Tasks 15, 16. ✓
- §6 testing invariants (count range, unique codice, cap 5-digit, schema, no missing keys, coverage) → Task 12 (+ schema pattern in Task 4, key-set assertion in Task 10). ✓
- §7 licenses MIT + CC-BY 4.0 + attribution → Task 16. ✓

**2. Placeholder scan:** No "TBD"/"add error handling"/"similar to Task N". The only intentionally open item is the CAP **source URL**, gated behind the Task 9 spike with an explicit decision-doc deliverable — the parser itself is fully specified. Production `sources.toml` (Task 16) depends on that spike's output, which is the correct dependency order.

**3. Type consistency:** `parse_*` return types match what `merge()` consumes (list[dict] + 4 dicts keyed by `codice`). `merge()` output key set matches `data/schema.json` required list and Task 10's key-set assertion. `emit`/`validate`/`build` all consume the same comune dict shape. `slugify` used identically in Task 2 and Task 11. `fetch` signature in Task 13 matches its use in Task 14 `_read_rows`. Consistent.

## Notes / open dependency

- **Task 9 is a gate:** the CAP (and possibly coordinate) source URL + license + join key must be decided and documented before the production `sources.toml` (Task 16) can be filled in. All code is testable against fixtures regardless, so Tasks 1–15 are unblocked.
