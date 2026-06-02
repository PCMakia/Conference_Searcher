import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Conference
from src.search.orchestrator import SearchOrchestrator


def test_ccf_deadlines_always_returns_us_upcoming():
    orch = SearchOrchestrator(wikicfp=MagicMock())
    orch.wikicfp.fetch_by_category.return_value = ([], "WikiCFP: 0 (mocked)")
    orch.wikicfp.fetch_by_keyword.return_value = ([], "")

    result = orch.search("Computer Vision", "")
    assert result.filtered_count >= 1
    assert any("CVPR" in c.acronym or "CVPR" in c.name for c in result.conferences)


def test_wikicfp_integration_with_fixture():
    from src.discovery.wikicfp_client import WikiCFPClient

    html = (Path(__file__).parent / "fixtures" / "wikicfp_sample.html").read_text(encoding="utf-8")
    client = WikiCFPClient()
    rows = client._parse_html(html)
    assert len(rows) >= 2

    us = [r for r in rows if "USA" in r.location or ", CA" in r.location]
    assert len(us) >= 2
