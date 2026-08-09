import pytest
from comuni_italiani.discover import latest_garda_zip, latest_posas_zip


def test_latest_garda_zip_picks_newest_from_html():
    html = (
        '<a href="/gi_db_comuni/gi_db_comuni-2026-01-02-aaaa.zip">old</a>'
        '<a href="/gi_db_comuni/gi_db_comuni-2026-08-07-8ef58.zip">new</a>'
    )
    assert latest_garda_zip(html=html) == (
        "https://www.gardainformatica.it/gi_db_comuni/gi_db_comuni-2026-08-07-8ef58.zip"
    )


def test_latest_garda_zip_no_link_raises():
    with pytest.raises(RuntimeError):
        latest_garda_zip(html="<html>nothing here</html>")


class _Resp:
    def __init__(self, code):
        self.status_code = code


class _FakeSession:
    def __init__(self, ok_year):
        self.ok_year = ok_year
        self.tried = []

    def head(self, url, timeout=0, allow_redirects=False):
        self.tried.append(url)
        return _Resp(200 if f"POSAS_{self.ok_year}_" in url else 404)


def test_latest_posas_zip_falls_back_to_available_year():
    s = _FakeSession(ok_year=2025)
    url = latest_posas_zip(2026, session=s)
    assert "POSAS_2025_" in url
    assert "POSAS_2026_" in s.tried[0]  # current year tried first


def test_latest_posas_zip_raises_when_none_found():
    s = _FakeSession(ok_year=1900)
    with pytest.raises(RuntimeError):
        latest_posas_zip(2026, session=s, span=3)
