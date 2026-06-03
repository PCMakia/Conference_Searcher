from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from src.discovery.ccf_deadlines import CCFDeadlinesClient
from src.discovery.web_search import WebSearchClient
from src.discovery.wikicfp_client import WikiCFPClient
from src.filters.conference_status import enrich_conference_status, is_upcoming, today
from src.filters.us_filter import is_us_location
from src.models import Conference
from src.ranking.link_resolver import LinkResolver
from src.ranking.prestige import PrestigeRanker
from src.search.semantic import SemanticSearch
from src.search.topics import wikicfp_category
from src.storage.cache import InMemoryCache


@dataclass
class SearchResult:
    conferences: List[Conference]
    status: str
    raw_count: int = 0
    filtered_count: int = 0


class SearchOrchestrator:
    def __init__(
        self,
        cache: Optional[InMemoryCache] = None,
        wikicfp: Optional[WikiCFPClient] = None,
        web_search: Optional[WebSearchClient] = None,
    ):
        self.cache = cache or InMemoryCache()
        self.wikicfp = wikicfp or WikiCFPClient(self.cache)
        self.web_search = web_search or WebSearchClient(self.cache)
        self.ccf = CCFDeadlinesClient()
        self.ranker = PrestigeRanker()
        self.link_resolver = LinkResolver(cache=self.cache)
        self.semantic = SemanticSearch()

    def search(
        self,
        topic: str,
        semantic_query: str = "",
        max_pages: int = 15,
    ) -> SearchResult:
        status_parts: List[str] = []
        ref = today()
        status_parts.append(f"Today: {ref.isoformat()}")

        category = wikicfp_category(topic)
        wiki_rows, wiki_status = self.wikicfp.fetch_by_category(category, max_pages=max_pages)
        status_parts.append(wiki_status)

        ccf_rows = self.ccf.load(topic)
        if ccf_rows:
            status_parts.append(f"CCF-deadlines: {len(ccf_rows)} bundled")

        conferences = self._merge_sources(wiki_rows, ccf_rows)

        if semantic_query.strip():
            kw_rows, kw_status = self.wikicfp.fetch_by_keyword(
                semantic_query.strip(), max_pages=5
            )
            status_parts.append(kw_status)
            conferences = self._merge_sources(conferences, kw_rows)

        web_rows, web_status = self.web_search.search(topic, semantic_query)
        status_parts.append(web_status)
        conferences = self._merge_sources(conferences, web_rows)

        raw_count = len(conferences)
        conferences = self._apply_filters(conferences, ref)
        filtered_count = len(conferences)

        if semantic_query.strip() and conferences:
            conferences = self.semantic.filter_by_query(conferences, semantic_query)
            filtered_count = len(conferences)

        for conf in conferences:
            enrich_conference_status(conf, ref)
            self.link_resolver.resolve(conf)

        ranked = self.ranker.rank(conferences)
        status = " | ".join(status_parts)
        status += f" | {raw_count} fetched -> {filtered_count} US upcoming"
        if raw_count > 0 and filtered_count == 0:
            status += " (try a different topic or broader search)"
        if raw_count == 0 and not ranked:
            status += " | No data — check internet connection"

        return SearchResult(
            conferences=ranked,
            status=status,
            raw_count=raw_count,
            filtered_count=filtered_count,
        )

    def _merge_sources(
        self,
        primary: List[Conference],
        secondary: List[Conference],
    ) -> List[Conference]:
        """Primary (WikiCFP) wins over secondary sources for the same venue."""
        by_key: dict[str, Conference] = {}
        for conf in primary:
            by_key[self._acronym_year_key(conf)] = conf

        for conf in secondary:
            key = self._acronym_year_key(conf)
            if key not in by_key:
                by_key[key] = conf
                continue
            existing = by_key[key]
            for field in (
                "attend_link",
                "external_link",
                "description",
            ):
                if not getattr(existing, field) and getattr(conf, field):
                    setattr(existing, field, getattr(conf, field))

        return list(by_key.values())

    @staticmethod
    def _acronym_year_key(c: Conference) -> str:
        acronym = (c.acronym or c.name).upper()
        acronym = re.sub(r"\s+\d{4}$", "", acronym).strip()
        years = re.findall(r"\b(20\d{2})\b", f"{c.name} {c.dates}")
        year = years[0] if years else ""
        return f"{acronym}:{year}"

    def _apply_filters(
        self,
        conferences: List[Conference],
        ref,
    ) -> List[Conference]:
        filtered: List[Conference] = []
        for conf in conferences:
            enrich_conference_status(conf, ref)
            if not is_us_location(conf.location):
                continue
            if not is_upcoming(conf, ref):
                continue
            filtered.append(conf)
        return filtered
