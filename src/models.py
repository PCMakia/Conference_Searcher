from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Conference:
    name: str
    acronym: str = ""
    dates: str = ""
    location: str = ""
    deadline: str = ""
    wikicfp_link: str = ""
    external_link: str = ""
    description: str = ""
    submit_link: str = ""
    attend_link: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    deadline_date: Optional[date] = None
    submission_open: bool = False
    attendance_open: bool = False
    prestige_score: float = 0.0
    prestige_label: str = ""
    core_rank: str = ""
    ccf_rank: str = ""
    source: str = "wikicfp"

    def display_key(self) -> str:
        key = (self.acronym or self.name).strip().upper()
        year = self.start_date.year if self.start_date else ""
        return f"{key}:{year}"

    def text_for_search(self) -> str:
        parts = [self.name, self.acronym, self.description, self.location]
        return " ".join(p for p in parts if p)
