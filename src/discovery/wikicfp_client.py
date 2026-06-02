from __future__ import annotations

import logging
import re
import time
from typing import List, Optional, Tuple
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from src.models import Conference
from src.storage.cache import Cache

logger = logging.getLogger(__name__)

BASE_URLS = ("http://www.wikicfp.com", "https://www.wikicfp.com")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_DELAY = 0.6
CACHE_VERSION = "v2"
MAX_PAGES_DEFAULT = 15


class WikiCFPClient:
    def __init__(self, cache: Optional[Cache] = None):
        self.cache = cache or Cache()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch_by_category(
        self,
        category: str,
        max_pages: int = MAX_PAGES_DEFAULT,
    ) -> Tuple[List[Conference], str]:
        """Return (conferences, status_message)."""
        conferences: List[Conference] = []
        errors: List[str] = []

        for page in range(1, max_pages + 1):
            url = f"/cfp/call?conference={quote_plus(category)}&page={page}"
            rows, err = self._fetch_page(url)
            if err:
                errors.append(err)
            if not rows:
                break
            conferences.extend(rows)
            time.sleep(REQUEST_DELAY)

        conferences = self._dedupe(conferences)
        status = self._status_message(len(conferences), errors)
        return conferences, status

    def fetch_by_keyword(
        self,
        keyword: str,
        max_pages: int = 5,
    ) -> Tuple[List[Conference], str]:
        conferences: List[Conference] = []
        errors: List[str] = []

        for page in range(1, max_pages + 1):
            url = (
                f"/cfp/servlet/tool.search?q={quote_plus(keyword)}"
                f"&year=t&page={page}"
            )
            rows, err = self._fetch_page(url)
            if err:
                errors.append(err)
            if not rows:
                break
            conferences.extend(rows)
            time.sleep(REQUEST_DELAY)

        conferences = self._dedupe(conferences)
        return conferences, self._status_message(len(conferences), errors)

    def _fetch_page(self, path: str) -> Tuple[List[Conference], Optional[str]]:
        cache_key = f"wikicfp:{CACHE_VERSION}:{path}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return [Conference(**row) for row in cached], None

        html, err = self._get_html(path)
        if err:
            return [], err
        if not html:
            return [], "Empty response from WikiCFP"

        conferences = self._parse_html(html)
        if conferences:
            self.cache.set(cache_key, [self._conf_to_dict(c) for c in conferences])
        return conferences, None

    def _get_html(self, path: str) -> Tuple[str, Optional[str]]:
        last_error: Optional[str] = None
        for base in BASE_URLS:
            url = f"{base}{path}"
            try:
                resp = self.session.get(url, timeout=25, allow_redirects=True)
                resp.raise_for_status()
                if len(resp.text) > 500 and ("wikicfp" in resp.text.lower() or "cfp" in resp.text.lower()):
                    return resp.text, None
            except requests.RequestException as exc:
                last_error = str(exc)
                logger.warning("WikiCFP fetch failed %s: %s", url, exc)
        return "", last_error or "Could not reach WikiCFP"

    def _parse_html(self, html: str) -> List[Conference]:
        soup = BeautifulSoup(html, "lxml")
        table = self._find_conference_table(soup)
        if table is None:
            return self._parse_tables_fallback(soup)
        return self._parse_multirow_table(table)

    def _find_conference_table(self, soup: BeautifulSoup):
        contsec = soup.find("div", class_="contsec")
        search_root = contsec if contsec else soup

        for table in search_root.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 3:
                continue
            headers = [td.get_text(strip=True).lower() for td in rows[0].find_all("td")]
            if headers and headers[0] == "event" and any(h == "when" for h in headers):
                return table
        return None

    def _parse_multirow_table(self, table) -> List[Conference]:
        """WikiCFP uses two rows per event: name row, then dates/location/deadline row."""
        conferences: List[Conference] = []
        rows = table.find_all("tr")[1:]
        i = 0
        while i < len(rows):
            if i + 1 >= len(rows):
                break
            row_name = rows[i]
            row_meta = rows[i + 1]
            tds_name = row_name.find_all("td")
            tds_meta = row_meta.find_all("td")

            link_tag = tds_name[0].find("a") if tds_name else None
            if not link_tag:
                i += 1
                continue

            name = link_tag.get_text(strip=True)
            wikicfp_link = ""
            href = link_tag.get("href", "")
            if href:
                wikicfp_link = href if href.startswith("http") else f"{BASE_URLS[0]}{href}"

            description = tds_name[1].get_text(" ", strip=True) if len(tds_name) > 1 else ""

            acronym = ""
            name_match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", name)
            if name_match:
                name, acronym = name_match.group(1).strip(), name_match.group(2).strip()
            elif re.match(r"^[A-Z][A-Za-z0-9\s\-]{0,30}\s+\d{4}$", name):
                parts = name.rsplit(" ", 1)
                if len(parts) == 2:
                    acronym, _year = parts[0].strip(), parts[1]

            dates = tds_meta[0].get_text(" ", strip=True) if len(tds_meta) > 0 else ""
            location = tds_meta[1].get_text(" ", strip=True) if len(tds_meta) > 1 else ""
            deadline = tds_meta[2].get_text(" ", strip=True) if len(tds_meta) > 2 else ""

            external = ""
            for a in row_name.find_all("a") + row_meta.find_all("a"):
                link = a.get("href", "")
                if link.startswith("http") and "wikicfp.com" not in link:
                    external = link
                    break

            conferences.append(
                Conference(
                    name=name,
                    acronym=acronym,
                    dates=dates,
                    location=location,
                    deadline=deadline,
                    wikicfp_link=wikicfp_link,
                    external_link=external,
                    description=description,
                )
            )
            i += 2

        return conferences

    def _parse_tables_fallback(self, soup: BeautifulSoup) -> List[Conference]:
        results: List[Conference] = []
        for table in soup.find_all("table"):
            parsed = self._parse_multirow_table(table)
            if len(parsed) >= 3:
                return parsed
            parsed_old = self._parse_single_row_table(table)
            if len(parsed_old) >= 3:
                results.extend(parsed_old)
        return results

    def _parse_single_row_table(self, table) -> List[Conference]:
        """Legacy single-row table layout."""
        rows = table.find_all("tr")
        if len(rows) < 2:
            return []

        conferences: List[Conference] = []
        for tr in rows[1:]:
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue

            link_tag = tds[0].find("a")
            if not link_tag:
                continue

            name = link_tag.get_text(strip=True)
            wikicfp_link = ""
            if link_tag.get("href"):
                href = link_tag["href"]
                wikicfp_link = href if href.startswith("http") else f"{BASE_URLS[0]}{href}"

            conferences.append(
                Conference(
                    name=name,
                    dates=tds[1].get_text(" ", strip=True),
                    location=tds[2].get_text(" ", strip=True),
                    deadline=tds[3].get_text(" ", strip=True),
                    wikicfp_link=wikicfp_link,
                )
            )
        return conferences

    @staticmethod
    def _status_message(count: int, errors: List[str]) -> str:
        if errors and count == 0:
            return f"WikiCFP error: {errors[0]}"
        if errors:
            return f"WikiCFP: {count} conferences (with warnings)"
        return f"WikiCFP: {count} conferences"

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
        for c in conferences:
            key = (c.name.lower(), c.dates, c.location.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
        return out
