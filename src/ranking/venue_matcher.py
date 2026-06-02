from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from typing import Dict, List

import yaml
from rapidfuzz import fuzz, process

from src.data.paths import data_dir, data_file
from src.models import Conference


@dataclass
class VenueRank:
    title: str
    acronym: str
    core_rank: str = ""
    ccf_rank: str = ""
    h5_index: float = 0.0
    homepage: str = ""
    in_ccf_deadlines: bool = False


class VenueMatcher:
    def __init__(self):
        self.core_venues: List[VenueRank] = self._load_core()
        self.ccf_venues: List[VenueRank] = self._load_ccf_yaml()
        self.aliases: Dict[str, str] = self._load_aliases()
        self._index: Dict[str, VenueRank] = {}
        self._build_index()

    def _load_aliases(self) -> Dict[str, str]:
        path = data_file("venue_aliases.json")
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    def _load_core(self) -> List[VenueRank]:
        path = data_file("core_rankings.csv")
        if not path.exists():
            return []
        venues: List[VenueRank] = []
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                rank = str(row.get("Rank", "")).strip()
                h5_raw = (row.get("Average Rating") or "").strip()
                try:
                    h5_val = float(h5_raw) if h5_raw else 0.0
                except ValueError:
                    h5_val = 0.0
                venues.append(
                    VenueRank(
                        title=str(row.get("Title", "")),
                        acronym=str(row.get("Acronym", "")).strip(),
                        core_rank=rank,
                        h5_index=h5_val,
                    )
                )
        return venues

    def _load_ccf_yaml(self) -> List[VenueRank]:
        ccf_dir = data_dir() / "ccf_deadlines"
        venues: List[VenueRank] = []
        if not ccf_dir.exists():
            return venues

        for yml_path in ccf_dir.glob("*.yml"):
            try:
                entries = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
            except (yaml.YAMLError, OSError):
                continue
            if not isinstance(entries, list):
                continue
            for entry in entries:
                rank = entry.get("rank") or {}
                confs = entry.get("confs") or []
                link = confs[0].get("link", "") if confs else ""
                venues.append(
                    VenueRank(
                        title=entry.get("title", ""),
                        acronym=entry.get("title", ""),
                        core_rank=str(rank.get("core", "")),
                        ccf_rank=str(rank.get("ccf", "")),
                        homepage=link,
                        in_ccf_deadlines=True,
                    )
                )
        return venues

    def _build_index(self) -> None:
        for v in self.core_venues + self.ccf_venues:
            if v.acronym:
                self._index[v.acronym.upper()] = v
            key = re.sub(r"[^a-z0-9]", "", v.title.lower())
            if key:
                self._index[key] = v

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        if text in self.aliases:
            return self.aliases[text].upper()
        return text.upper()

    def match(self, conf: Conference) -> VenueRank:
        candidates = []
        if conf.acronym:
            candidates.append(self._normalize(conf.acronym))
        name_upper = conf.name.upper()
        for token in re.findall(r"\b[A-Z]{2,12}\b", conf.name):
            candidates.append(token)

        for cand in candidates:
            if cand in self._index:
                return self._index[cand]

        all_venues = self.core_venues + self.ccf_venues
        choices = {v.acronym or v.title: v for v in all_venues if v.acronym or v.title}
        if not choices:
            return VenueRank(title="", acronym="")

        query = conf.acronym or conf.name
        result = process.extractOne(
            query,
            list(choices.keys()),
            scorer=fuzz.token_set_ratio,
            score_cutoff=75,
        )
        if result:
            return choices[result[0]]

        result = process.extractOne(
            conf.name,
            [v.title for v in all_venues if v.title],
            scorer=fuzz.partial_ratio,
            score_cutoff=80,
        )
        if result:
            for v in all_venues:
                if v.title == result[0]:
                    return v

        return VenueRank(title="", acronym="")
