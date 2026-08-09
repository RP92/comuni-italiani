import re
from typing import Iterable
from comuni_italiani.models import normalize_tipo

# Canonical ISTAT column names. The real "Elenco comuni italiani" CSV embeds
# newlines inside some quoted header cells and leaves trailing spaces, and the
# exact wording drifts slightly year to year. We therefore match on a
# whitespace-normalized form of both the header and these constants (see _norm),
# so "...sovracomunale \n(valida a fini statistici)" == "...sovracomunale (valida a fini statistici)".
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
C_PROV_COD = "Codice dell'Unità territoriale sovracomunale (valida a fini statistici)"
C_PROV_TIPO = "Tipologia di Unità territoriale sovracomunale"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# The ISTAT elenco encodes the sovracomunale typology as a numeric code.
_TIPO_BY_CODE = {
    "1": "provincia",
    "2": "provincia-autonoma",       # Trento, Bolzano
    "3": "citta-metropolitana",
    "4": "libero-consorzio",         # Sicilia
    "5": "decentramento-regionale",  # Friuli-Venezia Giulia (enti di decentramento regionale)
}


def _tipo(raw: str) -> str:
    raw = (raw or "").strip()
    if raw in _TIPO_BY_CODE:
        return _TIPO_BY_CODE[raw]
    return normalize_tipo(raw)  # tolerate free-text sources


def parse_anagrafica(rows: Iterable[dict]) -> list[dict]:
    out = []
    for raw in rows:
        r = {_norm(k): v for k, v in raw.items() if k is not None}
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
                "tipo": _tipo(r[C_PROV_TIPO]),
            },
        })
    return out
