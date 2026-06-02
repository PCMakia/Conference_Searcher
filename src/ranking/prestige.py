from __future__ import annotations

from typing import List

from src.models import Conference
from src.ranking.venue_matcher import VenueMatcher, VenueRank

CORE_SCORES = {
    "A*": 100,
    "A": 80,
    "A++": 100,
    "B": 50,
    "C": 20,
}

CCF_BONUS = {
    "A": 20,
    "B": 10,
    "C": 5,
}


def _normalize_rank(rank: str) -> str:
    if not rank:
        return ""
    r = rank.strip().upper().replace(" ", "")
    if r in ("A*", "A++", "A**"):
        return "A*"
    return r


def score_venue(venue: VenueRank) -> tuple[float, str]:
    core = _normalize_rank(venue.core_rank)
    score = CORE_SCORES.get(core, 0.0)

    ccf = venue.ccf_rank.strip().upper() if venue.ccf_rank else ""
    score += CCF_BONUS.get(ccf, 0)

    if venue.h5_index:
        score += min(venue.h5_index, 500) / 5.0

    if venue.in_ccf_deadlines and score < 15:
        score += 15

    label_parts = []
    if core:
        label_parts.append(f"CORE {core}")
    if ccf:
        label_parts.append(f"CCF {ccf}")
    if venue.h5_index:
        label_parts.append(f"h5≈{int(venue.h5_index)}")
    if not label_parts:
        label_parts.append("Unranked")

    return score, " / ".join(label_parts)


class PrestigeRanker:
    def __init__(self, matcher: VenueMatcher | None = None):
        self.matcher = matcher or VenueMatcher()

    def rank(self, conferences: List[Conference]) -> List[Conference]:
        for conf in conferences:
            venue = self.matcher.match(conf)
            score, label = score_venue(venue)
            conf.prestige_score = score
            conf.prestige_label = label
            conf.core_rank = venue.core_rank
            conf.ccf_rank = venue.ccf_rank

            if venue.homepage:
                if not conf.attend_link:
                    conf.attend_link = venue.homepage
                if not conf.external_link:
                    conf.external_link = venue.homepage

        def _sort_key(c: Conference):
            d = c.start_date or c.end_date
            date_ord = d.toordinal() if d else 999999
            return (-c.prestige_score, date_ord, c.name.lower())

        return sorted(conferences, key=_sort_key)
