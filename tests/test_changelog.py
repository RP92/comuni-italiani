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
