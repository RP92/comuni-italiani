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
