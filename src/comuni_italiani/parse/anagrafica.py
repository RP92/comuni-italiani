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
