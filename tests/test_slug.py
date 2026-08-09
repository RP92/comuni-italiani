import pytest
from comuni_italiani.slug import slugify

@pytest.mark.parametrize("name,expected", [
    ("Piemonte", "piemonte"),
    ("Emilia-Romagna", "emilia-romagna"),
    ("Friuli-Venezia Giulia", "friuli-venezia-giulia"),
    ("Valle d'Aosta/Vallée d'Aoste", "valle-d-aosta"),
    ("Trentino-Alto Adige/Südtirol", "trentino-alto-adige"),
])
def test_slugify(name, expected):
    assert slugify(name) == expected
