# comuni-italiani

Machine-readable dataset of all Italian comuni (municipalities) as of 2026,
built from official ISTAT sources. Includes names, codes, CAP (postal codes),
geographic coordinates, population, surface area, and administrative hierarchy
(regione / provincia / zona geografica).

Inspired by [`matteocontrini/comuni-json`](https://github.com/matteocontrini/comuni-json).

---

## Quick start — CDN (no install required)

```
https://cdn.jsdelivr.net/gh/RP92/comuni-italiani/data/comuni.json
```

The file is served directly from the `data/` directory of this repository via
jsDelivr. Pin to a specific commit for reproducibility:

```
https://cdn.jsdelivr.net/gh/RP92/comuni-italiani@<commit>/data/comuni.json
```

---

## Available formats

| File | Description |
|------|-------------|
| `data/comuni.json` | Full dataset — JSON array, one object per comune |
| `data/comuni.csv` | Same data in CSV (RFC 4180, UTF-8) |
| `data/comuni.ndjson` | Newline-delimited JSON, one object per line |
| `data/regioni/<slug>.json` | Per-regione split — one file per regione |
| `data/quality-report.json` | Pipeline validation report (count, CAP coverage). Schema and invariant failures cause the build to abort; the report's `errors` field is always an empty list on a successful run. |

---

## Schema

Each comune object has exactly the following 13 fields:

| Field | Type | Description |
|-------|------|-------------|
| `nome` | `string` | Official Italian name of the comune |
| `nomeAltraLingua` | `string \| null` | Name in a co-official language (German, French, Ladin, Slovenian), or `null` |
| `codice` | `string` | ISTAT numeric code, zero-padded to 6 digits (e.g. `"001272"`) |
| `codiceCatastale` | `string \| null` | Codice Catastale (Belfiore code) used in tax documents, e.g. `"L219"`, or `null` |
| `sigla` | `string \| null` | Provincia abbreviation (e.g. `"TO"`), or `null` for autonomous provinces |
| `cap` | `array[string]` | List of 5-digit postal codes (CAP). May contain more than one for large cities. Empty array if unknown (see CAP disclaimer below) |
| `capoluogo` | `boolean` | `true` if the comune is the capoluogo of its provincia / città metropolitana |
| `popolazione` | `integer \| null` | Resident population (latest ISTAT census/estimate), or `null` if unavailable |
| `superficie` | `number \| null` | Surface area in km², or `null` if unavailable |
| `coordinate` | `object \| null` | `{"lat": <number>, "lng": <number>}` centroid coordinates, or `null` if unavailable |
| `zona` | `object` | Geographic zone: `{"nome": <string>, "codice": <string>}` (e.g. Nord-ovest / 1) |
| `regione` | `object` | Region: `{"nome": <string>, "codice": <string>}` |
| `provincia` | `object` | Province: `{"nome": <string>, "codice": <string>, "sigla": <string \| null>, "tipo": <enum>}` where `tipo` is one of `"provincia"`, `"citta-metropolitana"`, `"libero-consorzio"`, `"provincia-autonoma"` |

---

## CAP disclaimer (best-effort)

CAP (postal codes) are sourced from **Garda Informatica — "Database dei comuni
italiani"** (MIT license). This is a community-maintained dataset derived from
official ISTAT codes; it is **not** an official Poste Italiane publication.

Known limitations:
- Large cities (Roma, Milano, Torino, …) have multiple CAPs per district;
  sub-municipal postal areas may be incomplete.
- No documented conflict-resolution methodology between ISTAT administrative
  changes and Poste Italiane routing updates.

Full source evaluation and decision rationale:
[`docs/cap-source.md`](docs/cap-source.md)

---

## Local rebuild

Requirements: Python 3.11+.

```bash
pip install -r requirements.txt
python -m comuni_italiani.cli sources.toml
```

Output is written to `data/`. A `.cache/` directory is used for downloaded
source files (re-runs skip re-downloading unless the cache is deleted).

Run the test suite:

```bash
pytest -q
```

---

## Licensing

**Code** (everything except `data/`): MIT — see [`LICENSE`](LICENSE).

**Data** (`data/`): Creative Commons Attribution 4.0 International (CC BY 4.0)
— see [`LICENSE-DATA`](LICENSE-DATA).  
Attribution: ISTAT and the sources documented in `LICENSE-DATA`.

---

## Credits

Inspired by [`matteocontrini/comuni-json`](https://github.com/matteocontrini/comuni-json).
Anagrafica, population, and surface-area data from [ISTAT](https://www.istat.it/).
CAP and coordinates from [Garda Informatica](https://www.gardainformatica.it/database-comuni-italiani).
