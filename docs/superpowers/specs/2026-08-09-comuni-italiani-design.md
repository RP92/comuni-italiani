# comuni-italiani — Design / Spec

- **Data:** 2026-08-09
- **Stato:** approvato in brainstorming, in attesa di review utente
- **Repo:** `comuni-italiani` (pubblico, GitHub, account RP92) — cartella locale `/home/casa/Scrivania/comuni-italiani`
- **Ispirazione:** [matteocontrini/comuni-json](https://github.com/matteocontrini/comuni-json)

## 1. Obiettivo e scope

Dataset pubblico e open dell'elenco completo dei comuni italiani **aggiornato al 2026**, sul
modello di comuni-json ma con:

- schema **rivisto e arricchito**,
- dati anagrafici **ufficiali ISTAT** (l'originale è fermo al 2020),
- **CAP best-effort** dalla migliore fonte open disponibile, con flag di confidenza,
- **auto-aggiornamento** via GitHub Actions (l'originale è statico),
- **formati multipli** (JSON / CSV / NDJSON) e **file spezzati per regione**.

### Fuori scope v1 (YAGNI)
- Pacchetto npm (possibile add-on futuro).
- Sito/demo di ricerca su GitHub Pages (possibile add-on futuro).
- API hostata.

Ognuno di questi resta un'aggiunta successiva, non blocca la v1.

## 2. Fonti dati

| Dato | Fonte | Note |
|------|-------|------|
| Anagrafica comuni (codice ISTAT, denominazione, denominazione altra lingua, regione, provincia + tipo, ripartizione/zona, sigla auto, **codice catastale**, flag capoluogo, NUTS) | ISTAT — "Codici statistici delle unità amministrative territoriali" | File ufficiale aggiornato più volte l'anno. Fonte primaria. |
| Popolazione residente | ISTAT — popolazione residente più recente | Non più il censimento 2011 dell'originale. |
| Superficie (km²) | ISTAT — superfici delle unità amministrative | |
| Coordinate (lat/lng municipio) | Dataset open supplementare (ISTAT / OpenStreetMap) | Enrichment; `null` dove mancante. |
| CAP | **Best-effort**: OpenStreetMap + dataset CAP open esistenti | Poste Italiane non pubblica una lista completa gratuita. Flag di confidenza. |

> **Spike di ricerca (in fase di piano):** individuare e validare la *migliore* fonte CAP open
> disponibile al 2026. È la parte meno garantita del dataset e va decisa con una verifica
> dedicata prima di consolidare la pipeline di enrichment.

## 3. Schema del comune

```json
{
  "nome": "Torino",
  "nomeAltraLingua": null,
  "codice": "001272",
  "codiceCatastale": "L219",
  "sigla": "TO",
  "cap": ["10121", "10122"],
  "capoluogo": true,
  "popolazione": 848196,
  "superficie": 130.06,
  "coordinate": { "lat": 45.0703, "lng": 7.6869 },
  "zona":      { "nome": "Nord-ovest", "codice": "1" },
  "regione":   { "nome": "Piemonte",  "codice": "01" },
  "provincia": { "nome": "Torino", "codice": "001", "sigla": "TO", "tipo": "citta-metropolitana" }
}
```

### Regole di schema
- **Schema stabile**: i campi sono sempre presenti. Un valore non disponibile è `null`
  (mai chiave omessa). Le liste (`cap`) sono `[]` se vuote.
- Miglioramenti rispetto a comuni-json: `nomeAltraLingua`, `capoluogo`, `superficie`,
  `coordinate`, `provincia.sigla`, `provincia.tipo`, popolazione recente.
- `provincia.tipo` ∈ { `provincia`, `citta-metropolitana`, `libero-consorzio`,
  `provincia-autonoma` }.
- `codice` = codice ISTAT del comune (stringa, zero-padded).
- Viene fornito un `schema.json` (JSON Schema draft 2020-12) usato anche in validazione.

> **Nota compatibilità:** lo schema è *rivisto* (non drop-in con comuni-json). Scelta esplicita.

## 4. Struttura repo e output

```
comuni-italiani/
├── data/
│   ├── comuni.json            # dataset completo
│   ├── comuni.csv
│   ├── comuni.ndjson
│   ├── regioni/
│   │   ├── piemonte.json      # split per regione (slug)
│   │   └── ...
│   └── schema.json            # JSON Schema di validazione
├── src/                       # pipeline Python
├── tests/                     # pytest
├── docs/
│   └── superpowers/specs/     # questa spec
├── .github/workflows/update.yml
├── README.md
├── LICENSE                    # codice (MIT)
├── LICENSE-DATA               # dati (CC-BY 4.0)
└── CHANGELOG.md
```

**Distribuzione:** i file in `data/` sono serviti automaticamente da jsDelivr / GitHub raw.
Il README documenta gli URL stabili di consumo (es. `cdn.jsdelivr.net/gh/RP92/comuni-italiani/data/comuni.json`).

## 5. Pipeline Python + automazione

Pipeline modulare, stadi disaccoppiati con interfacce chiare (ogni stadio testabile da solo):

```
download  → scarica le fonti grezze (ISTAT, coordinate, CAP) in cache locale
parse     → normalizza ogni fonte in una struttura intermedia uniforme
merge     → join per codice ISTAT (anagrafica = spina dorsale)
enrich    → aggancia CAP e coordinate; imposta flag di confidenza CAP
emit      → scrive comuni.json / .csv / .ndjson + split per regione
validate  → valida l'output contro schema.json + invarianti (vedi §6)
```

- Ogni stadio è un modulo Python isolato con input/output espliciti.
- `download` mette in cache le fonti per rendere le run riproducibili e offline-friendly.

### Automazione (GitHub Actions `update.yml`)
- **Trigger:** schedulato **mensile** + `workflow_dispatch` on-demand.
- Esegue l'intera pipeline; se l'output in `data/` cambia:
  - aggiorna il **CHANGELOG** con il diff (comuni **aggiunti / rimossi / modificati**),
  - apre una **Pull Request** automatica (non commit diretto), così le variazioni si
    revisionano prima del merge.
- Nessun cambiamento → nessuna PR.

## 6. Testing & invarianti di qualità

Test con **pytest**:

- Conteggio comuni entro un range atteso (~7.800–7.950) — guardia contro parsing rotto.
- **Unicità** del `codice` ISTAT.
- Ogni comune ha `regione` e `provincia` valide e coerenti (province ∈ regione).
- `cap`: ogni valore è 5 cifre numeriche.
- `sigla`: 1–2 lettere maiuscole.
- Validazione dell'intero output contro `schema.json`.
- Nessuna chiave mancante (solo `null` ammesso) — stabilità schema.
- Copertura CAP: report della % di comuni con almeno un CAP (metrica di qualità, non blocco).

## 7. Licenza & attribuzione

- **Codice:** MIT.
- **Dati:** CC-BY 4.0, con attribuzione a **ISTAT** e alle fonti CAP/coordinate.
- README con crediti a **comuni-json** come ispirazione e disclaimer sui CAP best-effort
  (completezza non garantita).

## 8. Decisioni prese (registro)

| Tema | Decisione |
|------|-----------|
| Fonte anagrafica | ISTAT ufficiale |
| Fonte CAP | Migliore open disponibile (spike in fase di piano), best-effort + flag |
| Stack build | Python |
| Schema | Rivisto e migliorato (non drop-in) |
| Aggiornamento | GitHub Actions mensile → PR automatica |
| Distribuzione | File in repo via CDN jsDelivr/raw + formati multipli + split per regione |
| Nome repo | `comuni-italiani` |
| Posizione locale | `/home/casa/Scrivania/comuni-italiani` (fuori dal gestionale) |

## 9. Rischi aperti

- **CAP**: qualità/completezza dipende dalla fonte open scelta; da validare nello spike.
- **Coordinate**: fonte open può non coprire il 100% dei comuni → `null` residui.
- **Formato fonti ISTAT**: possibili cambi di layout dei file ISTAT tra un anno e l'altro;
  lo stadio `parse` va tenuto tollerante e coperto da test.
