from __future__ import annotations

from typing import List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models import Conference


class SemanticSearch:
    def __init__(self):
        self._vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
        self._matrix = None
        self._conferences: List[Conference] = []

    def fit(self, conferences: List[Conference]) -> None:
        self._conferences = conferences
        if not conferences:
            self._matrix = None
            return
        corpus = [c.text_for_search() for c in conferences]
        self._matrix = self._vectorizer.fit_transform(corpus)

    def filter_by_query(
        self,
        conferences: List[Conference],
        query: str,
        min_score: float = 0.05,
    ) -> List[Conference]:
        query = (query or "").strip()
        if not query:
            return conferences

        self.fit(conferences)
        if self._matrix is None or not conferences:
            return []

        q_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self._matrix).flatten()

        scored: List[Tuple[Conference, float]] = [
            (conf, float(scores[i])) for i, conf in enumerate(conferences)
        ]
        filtered = [(c, s) for c, s in scored if s >= min_score]
        filtered.sort(key=lambda x: -x[1])
        return [c for c, _ in filtered]
