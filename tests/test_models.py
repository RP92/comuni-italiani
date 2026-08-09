import pytest
from comuni_italiani.models import normalize_tipo

@pytest.mark.parametrize("raw,expected", [
    ("Provincia", "provincia"),
    ("Città metropolitana", "citta-metropolitana"),
    ("Libero consorzio di comuni", "libero-consorzio"),
    ("Provincia autonoma", "provincia-autonoma"),
    ("  CITTA' METROPOLITANA ", "citta-metropolitana"),
])
def test_normalize_tipo(raw, expected):
    assert normalize_tipo(raw) == expected

def test_normalize_tipo_unknown_raises():
    with pytest.raises(ValueError):
        normalize_tipo("qualcosa")
