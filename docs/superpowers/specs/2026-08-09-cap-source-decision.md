# CAP Source Decision — 2026-08-09

## Decision summary

**Chosen primary source:** Garda Informatica — "Database dei comuni italiani"
**URL:** <https://www.gardainformatica.it/database-comuni-italiani>
**Download (2026-08-07 snapshot):** `https://www.gardainformatica.it/gi_db_comuni/gi_db_comuni-2026-08-07-8ef58.zip`

---

## Evaluated candidates

### 1. Garda Informatica — "Database dei comuni italiani" ✅ CHOSEN PRIMARY

| Attribute | Value |
|-----------|-------|
| License | **MIT** — explicit, redistribution permitted |
| Join key | `codice_istat` (alphanumeric, same convention as ISTAT) |
| Coverage | All active Italian comuni (~7,900+), including ceased ones with validity dates |
| Freshness | Updated **2026-08-07** (weekly automated procedure from official ISTAT sources) |
| CAP table | Dedicated `gi_cap` table pairing ISTAT code ↔ CAP; aggregated view `gi_comuni_cap` |
| Coordinates | Yes — latitude/longitude included in `gi_comuni` table |
| Formats | CSV, Excel (XLSX), SQL, JSON (single ZIP archive) |
| Cost | Free |

**Why chosen:** Only source evaluated that combines (a) an explicit permissive license allowing redistribution, (b) a direct ISTAT-codice ↔ CAP pairing, (c) fresh 2026 data, and (d) coverage of all ~7,900+ comuni. The MIT license is clear and unambiguous. The database is maintained with an automated pipeline from official ISTAT data, reducing stale-data risk.

**Bonus:** The same ZIP also contains geographic coordinates (`gi_comuni`), making it a viable unified source for both Task 8 (coordinates) and Task 9 (CAP).

**Known gaps / limitations:**
- The `gi_cap` table is community-maintained (Garda Informatica's automated pipeline), not directly from Poste Italiane; Poste Italiane does not publish a complete free list, so no dataset can claim 100% accuracy.
- Large cities (e.g. Roma, Milano, Torino) use multiple CAPs per district/street; these multi-CAP comuni should be covered through the one-to-many `gi_cap` structure, but completeness for sub-municipal postal areas is not guaranteed.
- No documented methodology for resolving conflicts between ISTAT administrative changes and Poste Italiane internal routing updates.

---

### 2. matteocontrini/comuni-json ❌ LICENSE UNCLEAR

| Attribute | Value |
|-----------|-------|
| License | Mixed / unclear — CAP data has **no license** applied; maintainer states source licenses are unknown |
| Coverage | 7,904 comuni |
| Freshness | Data as of **2020-01-01** (stale by ~6 years) |
| Join key | ISTAT `codice` + `cap` array per comune in JSON |

**Why rejected:** The maintainer explicitly states no license applies to the CAP portion because source licenses are unknown. This makes redistribution legally risky. Additionally the data is 6 years old, missing all administrative changes since January 2020.

---

### 3. opendatasicilia/comuni-italiani — cap.csv ❌ LICENSE UNSPECIFIED

| Attribute | Value |
|-----------|-------|
| License | **Not specified** in repository |
| Join key | `pro_com_t` (ISTAT code) + `cap` — two-column CSV, ideal format |
| Coverage | Claims all Italian comuni; source is Agid-iPA `amministrazioni.txt` |
| Freshness | Repository last updated December 2025 |

**Why rejected:** No license is declared, making redistribution legally ambiguous. The CAP data derives from `amministrazioni.txt` (public administration index), which covers only municipalities with a registered public-administration entry — this is likely incomplete for smaller comuni that are not registered in iPA. Could serve as a **fallback** for format validation given its clean two-column CSV structure.

---

### 4. OpenStreetMap (`addr:postcode` / `boundary postal_code`) ❌ INCOMPLETE

| Attribute | Value |
|-----------|-------|
| License | ODbL (redistribution permitted with share-alike) |
| Join key | `ref:ISTAT` tag on boundary relations |
| Coverage | Partial — `postal_code` tags on boundary relations are not systematically populated for all comuni; OSM Italy community forum confirms coverage gaps |
| Freshness | Continuously updated, but depends on volunteer contributions |

**Why rejected as primary:** Coverage is not comprehensive — OSM postal code tagging for Italian comuni boundaries is volunteer-driven and has known gaps. Overpass queries return only the comuni where mappers have explicitly added `postal_code` tags. ODbL share-alike could also complicate downstream use. Acceptable as a future cross-validation layer.

---

### 5. DarioCorno/database_comuni_italiani — MIT, but undated

| Attribute | Value |
|-----------|-------|
| License | MIT |
| Coverage | Unspecified count; appears complete |
| Freshness | Unknown — repository shows only 10 commits, no update timestamp visible |

**Why rejected:** License is acceptable but freshness is uncertain. Garda Informatica is preferred as it documents explicit update dates and an automated pipeline.

---

## Pre-mapping note

The Garda Informatica ZIP contains a `gi_cap.csv` (or SQL equivalent) with columns `codice_istat` and `cap`. Before calling `parse_cap()`, the `download`/`cli` pipeline stage must:

1. Extract the ZIP.
2. Read `gi_cap.csv` (or the CSV export of `gi_cap`).
3. Emit rows with columns renamed to `codice` and `cap` as expected by the parser.

The `codice_istat` field from Garda Informatica uses the same 6-character ISTAT alphanumeric format (e.g. `001272`) used throughout this project. No zero-padding transformation should be needed, but this must be verified at download time.

---

## Could this also serve Task 8 (coordinates)?

Yes. The `gi_comuni` table in the same ZIP includes latitude and longitude. Using a single source for both CAP and coordinates would reduce maintenance overhead. However, this is a decision for the Task 8 implementation; the coordinate parser is independent.
