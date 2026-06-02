import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.filters.conference_status import (
    enrich_conference_status,
    is_upcoming,
    parse_deadline_date,
    submission_status_label,
)
from src.models import Conference


def test_parse_iso_deadline():
    assert parse_deadline_date("2026-02-01 23:59:59") == date(2026, 2, 1)


def test_parse_wikicfp_deadline():
    assert parse_deadline_date("Jan 28, 2026 (Jan 23, 2026)") == date(2026, 1, 28)


def test_submission_closed_excluded_when_conference_over():
    conf = Conference(
        name="Past Conf",
        dates="Jan 1-5, 2020",
        location="Boston, MA, USA",
        deadline="Dec 1, 2019",
    )
    assert not is_upcoming(conf, ref=date(2026, 6, 2))


def test_submission_closed_but_conference_future_still_listed():
    conf = Conference(
        name="ICML 2026",
        dates="Jul 6, 2026 - Jul 12, 2026",
        location="Seoul, South Korea",
        deadline="Jan 28, 2026",
    )
    ref = date(2026, 6, 2)
    assert is_upcoming(conf, ref=ref)
    assert submission_status_label(conf, ref=ref) == "Closed"


def test_wrong_bundled_icml_us_excluded():
    conf = Conference(
        name="ICML 2026",
        dates="Jul 13-19, 2026",
        location="Honolulu, Hawaii, USA",
        deadline="2026-02-01 23:59:59",
        source="ccf_deadlines",
    )
    enrich_conference_status(conf, date(2026, 6, 2))
    assert submission_status_label(conf, date(2026, 6, 2)) == "Closed"
