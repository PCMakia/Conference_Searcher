from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

DEFAULT_TTL_SECONDS = 24 * 60 * 60


def _default_db_path() -> Path:
    base = Path.home() / ".conference_finder"
    base.mkdir(parents=True, exist_ok=True)
    return base / "cache.db"


class InMemoryCache:
    """Session-scoped cache cleared when the app process exits."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, cache_key: str) -> Optional[Any]:
        return self._store.get(cache_key)

    def set(self, cache_key: str, value: Any) -> None:
        self._store[cache_key] = value

    def delete(self, cache_key: str) -> None:
        self._store.pop(cache_key, None)

    def clear(self) -> None:
        self._store.clear()


class PersistentCache:
    """SQLite-backed HTTP cache with TTL (optional fallback, not used by default)."""

    def __init__(self, db_path: Optional[Path] = None, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.db_path = db_path or _default_db_path()
        self.ttl_seconds = ttl_seconds
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS http_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )

    def get(self, cache_key: str) -> Optional[Any]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload, created_at FROM http_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if not row:
            return None
        payload, created_at = row
        if time.time() - created_at > self.ttl_seconds:
            self.delete(cache_key)
            return None
        return json.loads(payload)

    def set(self, cache_key: str, value: Any) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO http_cache (cache_key, payload, created_at) VALUES (?, ?, ?)",
                (cache_key, json.dumps(value), time.time()),
            )

    def delete(self, cache_key: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM http_cache WHERE cache_key = ?", (cache_key,))


# Default cache for discovery clients: session-scoped, cleared on app exit.
Cache = InMemoryCache
