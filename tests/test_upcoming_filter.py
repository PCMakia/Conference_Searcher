import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.filters.upcoming_filter import is_upcoming, parse_conference_dates
from src.models import Conference


def test_parse_dates():
    start, end = parse_conference_dates("Jun 15-20, 2026")
    assert start is not None
    assert start.year == 2026


def test_upcoming_future():
    conf = Conference(name="Test", dates="Jun 15-20, 2030", location="Boston, MA, USA")
    assert is_upcoming(conf, today=date(2026, 1, 1))


def test_past_excluded():
    conf = Conference(name="Past", dates="Jan 1-5, 2020", location="Boston, MA, USA")
    assert not is_upcoming(conf, today=date(2026, 6, 1))
