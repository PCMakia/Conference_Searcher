from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from src.models import Conference

MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def parse_date_string(text: str) -> Optional[date]:
    if not text:
        return None
    text = text.strip()

    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%b %d, %Y", "%B %d, %Y", "%d %b %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    m = re.search(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+"
        r"(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?,?\s+(\d{4})",
        text,
        re.IGNORECASE,
    )
    if m:
        month_key = m.group(1).lower()[:3]
        month = MONTH_MAP.get(month_key) or MONTH_MAP.get(m.group(1).lower(), None)
        if month:
            return date(int(m.group(4)), month, int(m.group(2)))

    m = re.search(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+"
        r"(\d{1,2})\s*[-–]\s*(\d{1,2}),?\s+(\d{4})",
        text,
        re.IGNORECASE,
    )
    if m:
        month_key = m.group(1).lower()[:3]
        month = MONTH_MAP.get(month_key)
        if month:
            return date(int(m.group(4)), month, int(m.group(2)))

    m = re.search(r"\b(\d{4})\b", text)
    if m:
        year = int(m.group(1))
        if year >= 2000:
            return date(year, 12, 31)

    return None


def parse_conference_dates(dates_str: str) -> tuple[Optional[date], Optional[date]]:
    """Parse WikiCFP-style date ranges into start/end."""
    if not dates_str:
        return None, None

    text = dates_str.strip()
    if " - " in text and re.search(r"\d{4}", text):
        left, right = text.split(" - ", 1)
        start = parse_date_string(left.strip())
        end = parse_date_string(right.strip())
        if start and end:
            return start, end
        if start:
            return start, start

    start = parse_date_string(text)
    if start:
        m = re.search(
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+"
            r"(\d{1,2})\s*[-–]\s*(\d{1,2}),?\s+(\d{4})",
            dates_str,
            re.IGNORECASE,
        )
        if m:
            month_key = m.group(1).lower()[:3]
            month = MONTH_MAP.get(month_key)
            if month:
                end = date(int(m.group(4)), month, int(m.group(3)))
                return start, end
        return start, start

    return None, None


def enrich_dates(conf: Conference) -> Conference:
    start, end = parse_conference_dates(conf.dates)
    conf.start_date = start
    conf.end_date = end
    return conf


def is_upcoming(conf: Conference, today: Optional[date] = None) -> bool:
    """Delegate to conference_status (kept for backward-compatible imports)."""
    from src.filters.conference_status import is_upcoming as _is_upcoming

    return _is_upcoming(conf, today)
