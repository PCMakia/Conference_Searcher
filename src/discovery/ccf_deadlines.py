from __future__ import annotations

from typing import List

import yaml

from src.data.paths import data_dir
from src.models import Conference
from src.search.topics import TOPIC_TO_CCF_SUB

CCF_SUB_ALL = "ALL"


class CCFDeadlinesClient:
    """Load conferences from bundled CCF-deadlines-style YAML (fallback only)."""

    def load(self, topic: str = "All Computer Science") -> List[Conference]:
        ccf_dir = data_dir() / "ccf_deadlines"
        if not ccf_dir.exists():
            return []

        allowed_subs = TOPIC_TO_CCF_SUB.get(topic, {CCF_SUB_ALL})
        conferences: List[Conference] = []

        for yml_path in sorted(ccf_dir.glob("*.yml")):
            try:
                entries = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
            except (yaml.YAMLError, OSError):
                continue
            if not isinstance(entries, list):
                continue

            for entry in entries:
                sub = str(entry.get("sub", "")).upper()
                if CCF_SUB_ALL not in allowed_subs and sub not in allowed_subs:
                    continue
                if CCF_SUB_ALL not in allowed_subs and not sub:
                    continue

                title = entry.get("title", "")
                description = entry.get("description", "")

                for conf in entry.get("confs") or []:
                    place = conf.get("place", "")
                    date_str = conf.get("date", "")
                    link = conf.get("link", "")
                    year = conf.get("year", "")

                    deadline = ""
                    for item in conf.get("timeline") or []:
                        dl = item.get("deadline", "")
                        if dl and dl != "TBD":
                            deadline = dl
                            break

                    name = f"{title} {year}".strip() if year else title
                    conferences.append(
                        Conference(
                            name=name,
                            acronym=title,
                            dates=date_str,
                            location=place,
                            deadline=deadline,
                            attend_link=link,
                            external_link=link,
                            description=description,
                            source="ccf_deadlines",
                        )
                    )

        return conferences
