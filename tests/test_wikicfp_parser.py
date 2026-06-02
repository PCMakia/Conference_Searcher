import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.discovery.wikicfp_client import WikiCFPClient
from src.filters.us_filter import is_us_location
from src.filters.upcoming_filter import is_upcoming


FIXTURE = Path(__file__).parent / "fixtures" / "wikicfp_sample.html"


def test_parse_fixture():
    html = FIXTURE.read_text(encoding="utf-8")
    client = WikiCFPClient()
    rows = client._parse_html(html)
    assert len(rows) >= 2
    names = [r.name for r in rows]
    assert any("CVPR" in n for n in names)
    cvpr = next(r for r in rows if "CVPR" in r.name)
    assert "Denver" in cvpr.location
    assert "Jun" in cvpr.dates


def test_us_filter_on_parsed():
    html = FIXTURE.read_text(encoding="utf-8")
    client = WikiCFPClient()
    rows = client._parse_html(html)
    us_rows = [r for r in rows if is_us_location(r.location)]
    assert len(us_rows) == 2
    assert not any("Vienna" in r.location for r in us_rows)
