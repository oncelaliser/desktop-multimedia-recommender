from __future__ import annotations

import math
from collections import Counter

from common.utils import normalize_text


class SimilarityEngine:
    """Lightweight fallback similarity.

    MiniLM will later replace or augment this class without changing the UI.
    """

    def score(self, query: str, document: str) -> float:
        query_terms = self._terms(query)
        document_terms = self._terms(document)
        if not query_terms or not document_terms:
            return 0.0

        dot = sum(query_terms[token] * document_terms[token] for token in query_terms)
        query_norm = math.sqrt(sum(value * value for value in query_terms.values()))
        doc_norm = math.sqrt(sum(value * value for value in document_terms.values()))
        if query_norm == 0 or doc_norm == 0:
            return 0.0
        return dot / (query_norm * doc_norm)

    def _terms(self, text: str) -> Counter[str]:
        normalized = normalize_text(text)
        tokens = [token.strip(".,!?;:()[]{}\"'") for token in normalized.split()]
        return Counter(token for token in tokens if len(token) > 2)
