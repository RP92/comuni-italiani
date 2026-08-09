"""Resolve the latest download URLs for sources whose URL changes over time.

- Garda Informatica publishes a dated, hashed ZIP (…-YYYY-MM-DD-xxxxx.zip) linked
  from its database page; we scrape the newest link.
- ISTAT POSAS is published per year (POSAS_<year>_it_Comuni.zip); we probe from the
  current year downwards and use the first that exists.
"""
import re
import requests

_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
_GARDA_PAGE = "https://www.gardainformatica.it/database-comuni-italiani"
_GARDA_HOST = "https://www.gardainformatica.it"
_POSAS_TMPL = "https://demo.istat.it/data/posas/POSAS_{year}_it_Comuni.zip"
_GARDA_RE = re.compile(r"/gi_db_comuni/gi_db_comuni-\d{4}-\d{2}-\d{2}-[0-9a-z]+\.zip")


def _session(session):
    if session is None:
        session = requests.Session()
        session.headers["User-Agent"] = _UA
    return session


def latest_garda_zip(html=None, *, session=None, page_url=_GARDA_PAGE):
    """Return the absolute URL of the newest Garda gi_db_comuni ZIP."""
    if html is None:
        html = _session(session).get(page_url, timeout=60).text
    matches = _GARDA_RE.findall(html)
    if not matches:
        raise RuntimeError("no Garda gi_db_comuni .zip link found on the page")
    # The date (YYYY-MM-DD) embedded in the filename sorts chronologically as text.
    latest = sorted(set(matches), key=lambda p: re.search(r"\d{4}-\d{2}-\d{2}", p).group(0))[-1]
    return _GARDA_HOST + latest


def latest_posas_zip(current_year, *, session=None, span=4, template=_POSAS_TMPL):
    """Return the URL of the most recent available POSAS ZIP, trying current_year down."""
    s = _session(session)
    for year in range(current_year, current_year - span, -1):
        url = template.format(year=year)
        try:
            if s.head(url, timeout=30, allow_redirects=True).status_code == 200:
                return url
        except requests.RequestException:
            continue
    raise RuntimeError(
        f"no POSAS ZIP found in years {current_year}..{current_year - span + 1}"
    )
