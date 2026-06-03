from __future__ import annotations

import logging
import os
import re
from datetime import date
from typing import Any, List, Optional, Tuple

import requests

from src.filters.us_filter import US_STATES, is_us_location
from src.models import Conference
from src.search.topics import web_search_query
from src.storage.cache import Cache, InMemoryCache

logger = logging.getLogger(__name__)

CACHE_VERSION = "v1"
MAX_RESULTS = 10
GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"
SKIP_DOMAINS = ("wikicfp.com",)


class WebSearchClient:
    """Discover conferences via Google/DuckDuckGo web search."""

    def __init__(self, cache: Optional[InMemoryCache] = None):
        self.cache = cache or Cache()

    def search(self, topic: str, semantic_query: str = "") -> Tuple[List[Conference], str]:
        query = web_search_query(topic, semantic_query)
        cache_key = f"web_search:{CACHE_VERSION}:{query.lower()}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            conferences = [Conference(**row) for row in cached]
            return conferences, f"Web: {len(conferences)} conferences (session cache)"

        raw_hits = self._fetch_hits(query)
        conferences = self._hits_to_conferences(raw_hits)
        if conferences:
            self.cache.set(cache_key, [self._conf_to_dict(c) for c in conferences])
        if not raw_hits and not conferences:
            return [], "Web search: unavailable"
        return conferences, f"Web: {len(conferences)} conferences"

    def _fetch_hits(self, query: str) -> List[dict[str, Any]]:
        api_key = os.environ.get("GOOGLE_CSE_API_KEY", "").strip()
        cse_id = os.environ.get("GOOGLE_CSE_ID", "").strip()
        if api_key and cse_id:
            hits = self._fetch_google_cse(query, api_key, cse_id)
            if hits:
                return hits

        hits = self._fetch_ddgs(query, backend="google")
        if hits:
            return hits
        return self._fetch_ddgs(query, backend="duckduckgo")

    def _fetch_google_cse(
        self, query: str, api_key: str, cse_id: str
    ) -> List[dict[str, Any]]:
        try:
            resp = requests.get(
                GOOGLE_CSE_URL,
                params={"key": api_key, "cx": cse_id, "q": query, "num": MAX_RESULTS},
                timeout=25,
                headers={"User-Agent": "ConferenceFinder/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Google CSE fetch failed: %s", exc)
            return []

        items = data.get("items") or []
        hits: List[dict[str, Any]] = []
        for item in items[:MAX_RESULTS]:
            hits.append(
                {
                    "title": item.get("title", ""),
                    "href": item.get("link", ""),
                    "body": item.get("snippet", ""),
                }
            )
        return hits

    def _fetch_ddgs(self, query: str, backend: str) -> List[dict[str, Any]]:
        try:
            from ddgs import DDGS
        except ImportError:
            logger.warning("ddgs package not installed")
            return []

        try:
            with DDGS() as ddgs:
                results = list(
                    ddgs.text(
                        query,
                        max_results=MAX_RESULTS,
                        backend=backend,
                    )
                )
        except Exception as exc:
            logger.warning("DDGS %s search failed: %s", backend, exc)
            return []

        hits: List[dict[str, Any]] = []
        for item in results[:MAX_RESULTS]:
            hits.append(
                {
                    "title": item.get("title", ""),
                    "href": item.get("href", ""),
                    "body": item.get("body", ""),
                }
            )
        return hits

    def _hits_to_conferences(self, hits: List[dict[str, Any]]) -> List[Conference]:
        conferences: List[Conference] = []
        for hit in hits:
            conf = self._parse_hit(hit)
            if conf is not None:
                conferences.append(conf)
        return self._dedupe(conferences)

    def _parse_hit(self, hit: dict[str, Any]) -> Optional[Conference]:
        title = (hit.get("title") or "").strip()
        url = (hit.get("href") or "").strip()
        snippet = (hit.get("body") or "").strip()
        if not title or not url:
            return None

        if any(domain in url.lower() for domain in SKIP_DOMAINS):
            return None

        combined = f"{title} {snippet}"
        name, acronym = self._parse_name_acronym(title)
        location = self._extract_location(combined)
        dates = self._extract_dates(combined)
        deadline = self._extract_deadline(combined)

        if not location:
            return None

        if not dates:
            year = self._extract_future_year(combined)
            if year:
                dates = str(year)

        return Conference(
            name=name,
            acronym=acronym,
            dates=dates,
            location=location,
            deadline=deadline,
            external_link=url,
            attend_link=url,
            description=snippet,
            source="web_search",
        )

    @staticmethod
    def _parse_name_acronym(title: str) -> tuple[str, str]:
        cleaned = re.sub(r"\s*[-|–]\s*.*$", "", title).strip()
        name_match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", cleaned)
        if name_match:
            return name_match.group(1).strip(), name_match.group(2).strip()

        acronym_match = re.match(r"^([A-Z][A-Za-z0-9\-/]{1,20})\s+(\d{4})\b", cleaned)
        if acronym_match:
            return cleaned, acronym_match.group(1).strip()

        return cleaned, ""

    @staticmethod
    def _extract_location(text: str) -> str:
        if is_us_location(text):
            state_pattern = "|".join(re.escape(s) for s in sorted(US_STATES, key=len, reverse=True))
            m = re.search(
                rf"([A-Za-z .'-]+,\s*(?:{state_pattern}|[A-Z]{{2}})(?:,\s*USA)?)",
                text,
                re.IGNORECASE,
            )
            if m:
                return m.group(1).strip()

            for pattern in (r"\b([A-Za-z .'-]+,\s*[A-Z]{2})\b", r"\b(USA|United States)\b"):
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    return m.group(1).strip()

        return ""

    @staticmethod
    def _extract_dates(text: str) -> str:
        m = re.search(
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+"
            r"\d{1,2}(?:\s*[-–]\s*\d{1,2})?,?\s+\d{4}",
            text,
            re.IGNORECASE,
        )
        if m:
            return m.group(0).strip()

        m = re.search(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
            text,
            re.IGNORECASE,
        )
        if m:
            return m.group(0).strip()

        return ""

    @staticmethod
    def _extract_deadline(text: str) -> str:
        m = re.search(
            r"(?:deadline|submission|due)[:\s]+"
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
            text,
            re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()
        return ""

    @staticmethod
    def _extract_future_year(text: str) -> Optional[int]:
        ref_year = date.today().year
        years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
        future = [y for y in years if y >= ref_year]
        return max(future) if future else None

    @staticmethod
    def _conf_to_dict(conf: Conference) -> dict:
        return {
            "name": conf.name,
            "acronym": conf.acronym,
            "dates": conf.dates,
            "location": conf.location,
            "deadline": conf.deadline,
            "wikicfp_link": conf.wikicfp_link,
            "external_link": conf.external_link,
            "description": conf.description,
            "submit_link": conf.submit_link,
            "attend_link": conf.attend_link,
            "source": conf.source,
        }

    @staticmethod
    def _dedupe(conferences: List[Conference]) -> List[Conference]:
        seen: set[str] = set()
        out: List[Conference] = []
        for conf in conferences:
            key = (conf.name.lower(), conf.external_link.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(conf)
        return out
