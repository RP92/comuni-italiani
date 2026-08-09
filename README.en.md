# comuni-italiani

> 🇮🇹 **La versione italiana (principale) è in [`README.md`](README.md).**

Unofficial dataset of all Italian comuni (municipalities), with ISTAT
information and CAP (postal codes). Built from official ISTAT sources plus a
best-effort open CAP/coordinate source. Includes names, codes, CAP, geographic
coordinates, population, surface area, and administrative hierarchy
(regione / provincia / geographic zone).

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

## Example representation

The JSON file with all **7896** comuni is `comuni.json`. Each element looks
like this:

```json
{
  "nome": "Abano Terme",
  "nomeAltraLingua": null,
  "codice": "028001",
  "codiceCatastale": "A001",
  "sigla": "PD",
  "cap": ["35031"],
  "capoluogo": false,
  "popolazione": 20479,
  "superficie": 21.3082,
  "coordinate": { "lat": 45.3593736, "lng": 11.7886941 },
  "zona": { "nome": "Nord-est", "codice": "2" },
  "regione": { "nome": "Veneto", "codice": "05" },
  "provincia": { "nome": "Padova", "codice": "028", "sigla": "PD", "tipo": "provincia" }
}
```

`cap` is always a list: comuni with several postal areas carry all of them
(e.g. Roma has 73 CAP, Torino 33). 41 comuni have more than one CAP.

---

## Available formats

| File | Description |
|------|-------------|
| `data/comuni.json` | Full dataset — JSON array, one object per comune |
| `data/comuni.csv` | Same data in CSV (RFC 4180, UTF-8) |
| `data/comuni.ndjson` | Newline-delimited JSON, one object per line |
| `data/regioni/<slug>.json` | Per-regione split — one file per regione |
| `data/quality-report.json` | Pipeline validation report (count, CAP coverage). Schema and invariant failures abort the build; the report's `errors` field is always an empty list on a successful run. |

---

## Schema

Each comune object has exactly the following 13 fields:

| Field | Type | Description |
|-------|------|-------------|
| `nome` | `string` | Official Italian name of the comune |
| `nomeAltraLingua` | `string \| null` | Name in a co-official language (German, French, Ladin, Slovenian), or `null` |
| `codice` | `string` | ISTAT numeric code, zero-padded to 6 digits (e.g. `"001272"`) |
| `codiceCatastale` | `string \| null` | Codice Catastale (Belfiore code) used in tax documents, e.g. `"L219"`, or `null` |
| `sigla` | `string \| null` | Provincia abbreviation (e.g. `"TO"`), or `null` |
| `cap` | `array[string]` | List of 5-digit postal codes (CAP). May contain more than one for large cities. Empty array if unknown |
| `capoluogo` | `boolean` | `true` if the comune is the capoluogo of its provincia / città metropolitana |
| `popolazione` | `integer \| null` | Resident population (ISTAT), or `null` if unavailable |
| `superficie` | `number \| null` | Surface area in km², or `null` if unavailable |
| `coordinate` | `object \| null` | `{"lat": <number>, "lng": <number>}`, or `null` if unavailable |
| `zona` | `object` | Geographic zone: `{"nome": <string>, "codice": <string>}` |
| `regione` | `object` | Region: `{"nome": <string>, "codice": <string>}` |
| `provincia` | `object` | Province: `{"nome", "codice", "sigla": <string\|null>, "tipo": <enum>}` where `tipo` is one of `"provincia"`, `"citta-metropolitana"`, `"libero-consorzio"`, `"provincia-autonoma"`, `"decentramento-regionale"` |

---

## CAP disclaimer (best-effort)

CAP (postal codes) are sourced from **Garda Informatica — "Database dei comuni
italiani"** (MIT license), a community-maintained dataset derived from official
ISTAT codes; it is **not** an official Poste Italiane publication. Completeness
and correctness of the CAP cannot be guaranteed. Full rationale:
[`docs/cap-source.md`](docs/cap-source.md).

---

## Local rebuild

Requirements: Python 3.11+.

```bash
pip install .
python -m comuni_italiani.cli sources.toml
```

Output is written to `data/`. Run the tests with `pytest -q`.

---

## Licensing

**Code** (everything except `data/`): MIT — see [`LICENSE`](LICENSE).
**Data** (`data/`): CC BY 4.0 — see [`LICENSE-DATA`](LICENSE-DATA).
Attribution: ISTAT and the sources documented in `LICENSE-DATA`.

---

## Credits

Inspired by [`matteocontrini/comuni-json`](https://github.com/matteocontrini/comuni-json).
Anagrafica, population and surface-area data from [ISTAT](https://www.istat.it/).
CAP and coordinates from [Garda Informatica](https://www.gardainformatica.it/database-comuni-italiani).
