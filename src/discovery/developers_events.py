from __future__ import annotations

import re
from typing import Dict, List, Optional

import requests

from src.models import Conference
from src.storage.cache import Cache

API_URL = "https://developers.events/all-cfps.json"


class DevelopersEventsClient:
    """Optional supplement for CFP URLs (dev/tech conferences)."""

    def __init__(self, cache: Optional[Cache] = None):
        self.cache = cache or Cache()

    def fetch_cfps(self) -> List[dict]:
        cache_key = "developers.events:cfps"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            resp = requests.get(API_URL, timeout=30, headers={"User-Agent": "ConferenceFinder/1.0"})
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError):
            return []

        if isinstance(data, list):
            self.cache.set(cache_key, data)
            return data
        return []

    def match_by_name(self, name: str, acronym: str = "") -> Optional[dict]:
        name_lower = name.lower()
        acr = acronym.lower()
        for item in self.fetch_cfps():
            conf_name = (item.get("name") or item.get("title") or "").lower()
            if acr and acr in conf_name:
                return item
            if name_lower and name_lower[:12] in conf_name:
                return item
        return None

    def enrich_links(self, conf: Conference) -> Conference:
        match = self.match_by_name(conf.name, conf.acronym)
        if not match:
            return conf

        cfp = match.get("cfp") or {}
        if isinstance(cfp, dict):
            url = cfp.get("url") or cfp.get("link")
            if url and not conf.submit_link:
                conf.submit_link = url

        if not conf.attend_link:
            conf.attend_link = match.get("website") or match.get("homepage") or ""

        if not conf.location and match.get("location"):
            loc = match["location"]
            if isinstance(loc, dict):
                conf.location = ", ".join(
                    str(loc.get(k, "")) for k in ("city", "country") if loc.get(k)
                )
            else:
                conf.location = str(loc)

        return conf
