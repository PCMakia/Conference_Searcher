from __future__ import annotations

from typing import Optional

from src.discovery.developers_events import DevelopersEventsClient
from src.models import Conference
from src.storage.cache import InMemoryCache


class LinkResolver:
    def __init__(
        self,
        dev_events: DevelopersEventsClient | None = None,
        cache: Optional[InMemoryCache] = None,
    ):
        self.dev_events = dev_events or DevelopersEventsClient(cache=cache)

    def resolve(self, conf: Conference) -> Conference:
        # WikiCFP event page often has the real CFP link
        if conf.wikicfp_link and not conf.submit_link:
            conf.submit_link = conf.wikicfp_link

        if conf.external_link and not conf.attend_link:
            conf.attend_link = conf.external_link

        if not conf.submit_link and conf.attend_link:
            base = conf.attend_link.rstrip("/")
            for suffix in ("/cfp", "/call-for-papers", "/submission", "/submissions"):
                conf.submit_link = base + suffix
                break

        conf = self.dev_events.enrich_links(conf)

        if not conf.attend_link and conf.external_link:
            conf.attend_link = conf.external_link

        if not conf.submit_link and conf.wikicfp_link:
            conf.submit_link = conf.wikicfp_link

        return conf
