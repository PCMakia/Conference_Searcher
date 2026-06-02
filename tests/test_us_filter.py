import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.filters.us_filter import is_us_location


def test_usa_patterns():
    assert is_us_location("Denver, Colorado, USA")
    assert is_us_location("San Diego, CA, USA")
    assert is_us_location("Boston, MA, United States")


def test_non_us():
    assert not is_us_location("Vienna, Austria")
    assert not is_us_location("")
    assert not is_us_location("London, UK")
