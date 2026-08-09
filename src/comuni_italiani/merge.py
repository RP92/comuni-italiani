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
