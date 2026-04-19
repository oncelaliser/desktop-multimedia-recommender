from __future__ import annotations

from core.chatbot.intent_parser import UserIntent
from core.recommendation.similarity import SimilarityEngine
from data.models.media_item import MediaItem


class ScoringEngine:
    def __init__(self, similarity_engine: SimilarityEngine | None = None) -> None:
        self.similarity_engine = similarity_engine or SimilarityEngine()

    def score(self, intent: UserIntent, media: MediaItem) -> float:
        semantic = self.similarity_engine.score(
            intent.raw_text,
            " ".join([media.title, media.description, " ".join(media.genres), " ".join(media.moods)]),
        )
        genre_score = self._overlap(intent.genres, media.genres)
        mood_score = self._overlap(intent.moods, media.moods)
        type_score = 1.0 if intent.media_type and intent.media_type == media.media_type else 0.0
        if not intent.media_type:
            type_score = 0.5
        era_score = self._era_score(intent.era, media.release_year)
        rating_score = (media.rating or 0) / 10
        popularity_score = media.popularity or 0

        final = (
            0.35 * semantic
            + 0.20 * genre_score
            + 0.15 * type_score
            + 0.10 * mood_score
            + 0.10 * era_score
            + 0.05 * rating_score
            + 0.05 * popularity_score
        )
        return round(final * 100, 1)

    def _overlap(self, wanted: list[str], actual: list[str]) -> float:
        if not wanted:
            return 0.5
        if not actual:
            return 0.0
        return len(set(wanted) & set(actual)) / len(set(wanted))

    def _era_score(self, era: str | None, year: int | None) -> float:
        if not era:
            return 0.5
        if not year:
            return 0.0
        if era == "1990s" and 1990 <= year <= 1999:
            return 1.0
        if era == "1980s" and 1980 <= year <= 1989:
            return 1.0
        if era == "2000s" and 2000 <= year <= 2009:
            return 1.0
        return 0.0
