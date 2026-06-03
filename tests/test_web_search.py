import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.discovery.web_search import WebSearchClient
from src.storage.cache import InMemoryCache


SAMPLE_HITS = [
    {
        "title": "CVPR 2026 - Call for Papers",
        "href": "https://cvpr.thecvf.com/cfp",
        "body": "IEEE/CVF CVPR 2026 in Denver, CO, USA. Deadline: Nov 14, 2025.",
    },
    {
        "title": "WikiCFP - CVPR",
        "href": "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=123",
        "body": "Denver, CO, USA conference listing.",
    },
    {
        "title": "NeurIPS 2025",
        "href": "https://neurips.cc",
        "body": "Machine learning conference in Vancouver, Canada.",
    },
]


def test_web_search_parses_us_conference():
    client = WebSearchClient(cache=InMemoryCache())
    conferences = client._hits_to_conferences(SAMPLE_HITS)
    assert len(conferences) == 1
    conf = conferences[0]
    assert "CVPR" in conf.name or conf.acronym == "CVPR"
    assert "Denver" in conf.location or "CO" in conf.location
    assert conf.source == "web_search"
    assert conf.external_link.startswith("https://cvpr")


def test_web_search_skips_wikicfp_urls():
    client = WebSearchClient(cache=InMemoryCache())
    conf = client._parse_hit(SAMPLE_HITS[1])
    assert conf is None


def test_web_search_session_cache_reuse():
    cache = InMemoryCache()
    client = WebSearchClient(cache=cache)

    with patch.object(client, "_fetch_hits", return_value=SAMPLE_HITS) as fetch_mock:
        rows1, status1 = client.search("Computer Vision", "")
        rows2, status2 = client.search("Computer Vision", "")

    assert len(rows1) == 1
    assert len(rows2) == 1
    assert fetch_mock.call_count == 1
    assert "session cache" in status2


def test_web_search_query_includes_topic_and_year():
    from src.search.topics import web_search_query

    q = web_search_query("Computer Vision", "3D reconstruction")
    assert "Computer Vision" in q
    assert "3D reconstruction" in q
    assert "USA" in q
    assert "call for papers" in q
