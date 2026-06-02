"""Compare conference dates against today for filtering and UI status labels."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from src.filters.upcoming_filter import enrich_dates, parse_date_string
from src.models import Conference


def today() -> date:
    """Today's date (local). All open/closed checks use this."""
    return date.today()


def parse_deadline_date(deadline_text: str) -> Optional[date]:
    """Parse submission deadline from WikiCFP or CCF-deadlines strings."""
    if not deadline_text or deadline_text.strip().upper() == "TBD":
        return None

    text = deadline_text.strip()

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    # WikiCFP: "Jan 28, 2026 (Jan 23, 2026)" — use the primary (first) date
    primary = re.split(r"\s*\(", text, maxsplit=1)[0].strip()
    parsed = parse_date_string(primary)
    if parsed:
        return parsed

    return parse_date_string(text)


def enrich_conference_status(conf: Conference, ref: Optional[date] = None) -> Conference:
    """Fill parsed deadline_date and open flags on the conference."""
    ref = ref or today()
    enrich_dates(conf)
    conf.deadline_date = parse_deadline_date(conf.deadline)

    conf.submission_open = conf.deadline_date is not None and conf.deadline_date >= ref
    conf.attendance_open = (
        (conf.end_date is not None and conf.end_date >= ref)
        or (conf.start_date is not None and conf.start_date >= ref)
    )
    return conf


def is_upcoming(conf: Conference, ref: Optional[date] = None) -> bool:
    """
    Include conference if it has not ended yet OR paper submission is still open.

    Compared against today() in conference_status.today().
    """
    ref = ref or today()
    enrich_conference_status(conf, ref)

    if conf.end_date and conf.end_date < ref:
        return False

    if conf.submission_open:
        return True

    if conf.attendance_open:
        return True

    return False


def submission_status_label(conf: Conference, ref: Optional[date] = None) -> str:
    ref = ref or today()
    enrich_conference_status(conf, ref)
    if conf.deadline_date is None:
        return "Unknown"
    return "Open" if conf.submission_open else "Closed"


def attendance_status_label(conf: Conference, ref: Optional[date] = None) -> str:
    ref = ref or today()
    enrich_conference_status(conf, ref)
    if conf.start_date is None and conf.end_date is None:
        return "Unknown"
    return "Open" if conf.attendance_open else "Closed"


def submit_link_enabled(conf: Conference, ref: Optional[date] = None) -> bool:
    """Only offer submit link when deadline is open and a URL exists."""
    ref = ref or today()
    enrich_conference_status(conf, ref)
    return bool(conf.submit_link) and conf.submission_open


def attend_link_enabled(conf: Conference, ref: Optional[date] = None) -> bool:
    ref = ref or today()
    enrich_conference_status(conf, ref)
    return bool(conf.attend_link) and conf.attendance_open
