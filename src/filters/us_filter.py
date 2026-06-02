from __future__ import annotations

import re

US_PATTERNS = [
    r"\bUSA\b",
    r"\bU\.S\.A\.?\b",
    r"\bUnited States\b",
    r"\bU\.S\.?\b",
    r",\s*US\b",
    r"\bUS\s*\)",
]

US_STATES = {
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming", "District of Columbia",
    "DC",
}

_COMPILED = [re.compile(p, re.IGNORECASE) for p in US_PATTERNS]


def is_us_location(location: str, *, physical_only: bool = True) -> bool:
    """Return True if location string indicates a US venue."""
    if not location or not location.strip():
        return False

    text = location.strip()
    lower = text.lower()

    if any(p.search(text) for p in _COMPILED):
        return True

    us_state_codes = {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
        "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
        "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
        "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
        "WI", "WY", "DC",
    }
    m = re.search(r",\s*([A-Z]{2})\b", text)
    if m and m.group(1) in us_state_codes:
        return True

    for state in US_STATES:
        if re.search(rf"\b{re.escape(state)}\b", text, re.IGNORECASE):
            if re.search(rf",\s*{re.escape(state)}\b", text, re.IGNORECASE):
                return True
            if re.search(rf"\b{re.escape(state)},\s*USA", text, re.IGNORECASE):
                return True
            if state in ("Washington", "New York", "Georgia") and "USA" in text.upper():
                return True

    if not physical_only and re.search(r"\b(online|virtual)\b", lower):
        if re.search(r"\bUS\b", text, re.IGNORECASE):
            return True

    return False
