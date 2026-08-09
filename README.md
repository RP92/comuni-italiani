# comuni-italiani

> 🇬🇧 **English version: [`README.en.md`](README.en.md).**

Database **non ufficiale** dei comuni italiani, con informazioni ISTAT e CAP.
Costruito da fonti ufficiali ISTAT più una fonte open (best-effort) per CAP e
coordinate. Contiene denominazioni, codici, CAP, coordinate geografiche,
popolazione, superficie e la gerarchia amministrativa
(regione / provincia / zona geografica).

Ispirato a [`matteocontrini/comuni-json`](https://github.com/matteocontrini/comuni-json).

---

## Avvio rapido — CDN (nessuna installazione)

```
https://cdn.jsdelivr.net/gh/RP92/comuni-italiani/data/comuni.json
```

Il file è servito direttamente dalla cartella `data/` di questo repository
tramite jsDelivr. Per riproducibilità puoi agganciarti a un commit specifico:

```
https://cdn.jsdelivr.net/gh/RP92/comuni-italiani@<commit>/data/comuni.json
```

---

## Rappresentazione di esempio

Il file JSON con tutti i **7896** comuni è `comuni.json`. Ogni elemento è fatto
così:

```json
{
  "nome": "Abano Terme",
  "nomeAltraLingua": null,
  "codice": "028001",
  "codiceCatastale": "A001",
  "sigla": "PD",
  "cap": ["35031"],
  "capoluogo": false,
  "popolazione": 20433,
  "superficie": 21.3082,
  "coordinate": { "lat": 45.3593736, "lng": 11.7886941 },
  "zona": { "nome": "Nord-est", "codice": "2" },
  "regione": { "nome": "Veneto", "codice": "05" },
  "provincia": { "nome": "Padova", "codice": "028", "sigla": "PD", "tipo": "provincia" }
}
```

Il campo `cap` è **sempre una lista**: i comuni con più aree postali li
contengono tutti (es. Roma ha 73 CAP, Torino 33). In tutto 41 comuni hanno più
di un CAP.

---

## Formati disponibili

| File | Descrizione |
|------|-------------|
| `data/comuni.json` | Dataset completo — array JSON, un oggetto per comune |
| `data/comuni.csv` | Stessi dati in CSV (RFC 4180, UTF-8) |
| `data/comuni.ndjson` | JSON delimitato da newline, un oggetto per riga |
| `data/regioni/<slug>.json` | Suddivisione per regione — un file per regione |
| `data/quality-report.json` | Report di validazione della pipeline (conteggio, copertura CAP). Errori di schema o di invariante interrompono la build; il campo `errors` del report è sempre una lista vuota in caso di run riuscito. |

---

## Schema

Ogni comune ha esattamente questi 13 campi:

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `nome` | `string` | Denominazione italiana ufficiale del comune |
| `nomeAltraLingua` | `string \| null` | Denominazione in lingua co-ufficiale (tedesco, francese, ladino, sloveno), oppure `null` |
| `codice` | `string` | Codice ISTAT numerico, con zero-padding a 6 cifre (es. `"001272"`) |
| `codiceCatastale` | `string \| null` | Codice Catastale (codice Belfiore) usato nei documenti fiscali, es. `"L219"`, oppure `null` |
| `sigla` | `string \| null` | Sigla della provincia (es. `"TO"`), oppure `null` |
| `cap` | `array[string]` | Lista di CAP a 5 cifre. Può contenerne più di uno per le grandi città. Lista vuota se sconosciuto |
| `capoluogo` | `boolean` | `true` se il comune è capoluogo della sua provincia / città metropolitana |
| `popolazione` | `integer \| null` | Popolazione residente (ISTAT), oppure `null` se non disponibile |
| `superficie` | `number \| null` | Superficie in km², oppure `null` se non disponibile |
| `coordinate` | `object \| null` | `{"lat": <number>, "lng": <number>}`, oppure `null` se non disponibile |
| `zona` | `object` | Zona geografica: `{"nome": <string>, "codice": <string>}` (es. Nord-ovest / 1) |
| `regione` | `object` | Regione: `{"nome": <string>, "codice": <string>}` |
| `provincia` | `object` | Provincia: `{"nome": <string>, "codice": <string>, "sigla": <string \| null>, "tipo": <enum>}` dove `tipo` è uno tra `"provincia"`, `"citta-metropolitana"`, `"libero-consorzio"`, `"provincia-autonoma"`, `"decentramento-regionale"` (Friuli-Venezia Giulia) |

---

## Nota sui CAP (best-effort)

I CAP provengono da **Garda Informatica — "Database dei comuni italiani"**
(licenza MIT): un dataset mantenuto dalla community e derivato dai codici
ufficiali ISTAT, **non** una pubblicazione ufficiale di Poste Italiane. La
completezza e la correttezza dei CAP non possono essere garantite.

Limiti noti:
- Le grandi città (Roma, Milano, Torino, …) hanno più CAP per zona; alcune
  aree postali sub-comunali possono essere incomplete.
- Non esiste una metodologia documentata di riconciliazione tra le variazioni
  amministrative ISTAT e gli aggiornamenti di recapito di Poste Italiane.

Valutazione delle fonti e motivazioni:
[`docs/cap-source.md`](docs/cap-source.md).

---

## Rigenerare in locale

Requisiti: Python 3.11+.

```bash
pip install .
python -m comuni_italiani.cli sources.toml
```

L'output viene scritto in `data/`. Una cartella `.cache/` conserva i file
sorgente scaricati (le esecuzioni successive non riscaricano finché la cache
non viene cancellata).

Esegui i test:

```bash
pytest -q
```

---

## Licenze

**Codice** (tutto tranne `data/`): MIT — vedi [`LICENSE`](LICENSE).

**Dati** (`data/`): Creative Commons Attribution 4.0 International (CC BY 4.0)
— vedi [`LICENSE-DATA`](LICENSE-DATA).
Attribuzione: ISTAT e le fonti documentate in `LICENSE-DATA`.

---

## Crediti

Ispirato a [`matteocontrini/comuni-json`](https://github.com/matteocontrini/comuni-json).
Anagrafica, popolazione e superficie da [ISTAT](https://www.istat.it/).
CAP e coordinate da [Garda Informatica](https://www.gardainformatica.it/database-comuni-italiani).
