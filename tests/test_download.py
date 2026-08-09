from pathlib import Path
from comuni_italiani.download import fetch

class FakeResp:
    def __init__(self, content): self.content = content
    def raise_for_status(self): pass

class FakeSession:
    def __init__(self): self.calls = 0
    def get(self, url, timeout=0):
        self.calls += 1
        return FakeResp(b"hello")

def test_fetch_writes_and_caches(tmp_path):
    s = FakeSession()
    dest = tmp_path / "f.bin"
    p1 = fetch("http://x", dest, session=s)
    assert p1.read_bytes() == b"hello"
    # second call uses cache, no new request
    fetch("http://x", dest, session=s)
    assert s.calls == 1

def test_fetch_force_refetches(tmp_path):
    s = FakeSession()
    dest = tmp_path / "f.bin"
    fetch("http://x", dest, session=s)
    fetch("http://x", dest, session=s, force=True)
    assert s.calls == 2
