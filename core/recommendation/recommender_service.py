from __future__ import annotations

import logging

from core.chatbot.intent_parser import IntentParser, UserIntent
from core.recommendation.explanation_builder import ExplanationBuilder
from core.recommendation.sample_catalog import SAMPLE_MEDIA
from core.recommendation.scoring_engine import ScoringEngine
from data.models.media_item import MediaItem
from data.models.recommendation import Recommendation

logger = logging.getLogger(__name__)


class RecommenderService:
    def __init__(
        self,
        catalog: list[MediaItem] | None = None,
        intent_parser: IntentParser | None = None,
        scoring_engine: ScoringEngine | None = None,
        explanation_builder: ExplanationBuilder | None = None,
        tmdb_client=None,
        omdb_client=None,
        spotify_client=None,
        media_repository=None,
    ) -> None:
        self._static_catalog = catalog or SAMPLE_MEDIA
        self.intent_parser = intent_parser or IntentParser()
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.explanation_builder = explanation_builder or ExplanationBuilder()
        self._tmdb = tmdb_client
        self._omdb = omdb_client
        self._spotify = spotify_client
        self._repo = media_repository

    def recommend(
        self,
        user_prompt: str,
        selected_media_type: str = "Any",
        limit: int = 5,
    ) -> list[Recommendation]:
        intent = self.intent_parser.parse(user_prompt)
        catalog = self._build_catalog(intent, selected_media_type)
        catalog = self._filter_by_media_type(catalog, selected_media_type)

        # Deduplicate by normalized title+type across sources (prefer higher-rated)
        seen_titles: dict[str, Recommendation] = {}
        for media in catalog:
            key = f"{media.title.lower().strip()}|{media.media_type}"
            rec = Recommendation(
                media=media,
                score=self.scoring_engine.score(intent, media),
                reason=self.explanation_builder.build(intent, media),
            )
            if key not in seen_titles or rec.score > seen_titles[key].score:
                seen_titles[key] = rec

        return sorted(seen_titles.values(), key=lambda item: item.score, reverse=True)[:limit]

    def _build_catalog(self, intent: UserIntent, selected_media_type: str) -> list[MediaItem]:
        media_type = selected_media_type.lower()

        if media_type == "music" and self._spotify:
            try:
                live = self._fetch_from_spotify(intent)
                if live:
                    if self._repo:
                        self._repo.save_many(live)
                    return live + self._static_catalog
            except Exception as exc:
                logger.warning("Spotify fetch failed: %s", exc)

        # TMDB as primary source for movies/series
        if self._tmdb and media_type != "music":
            try:
                live = self._fetch_from_tmdb(intent, selected_media_type)
                if live:
                    if self._repo:
                        self._repo.save_many(live)
                    if intent.language:
                        # Include static catalog items that match the requested language
                        lang_static = [i for i in self._static_catalog if i.language == intent.language]
                        return live + lang_static
                    return live + self._static_catalog
            except Exception as exc:
                logger.warning("TMDB fetch failed, falling back: %s", exc)

        # OMDb as fallback
        if self._omdb and media_type != "music":
            try:
                live = self._fetch_from_omdb(intent, selected_media_type)
                if live:
                    if self._repo:
                        self._repo.save_many(live)
                    return live + self._static_catalog
            except Exception as exc:
                logger.warning("OMDb fetch failed: %s", exc)

        if self._repo:
            cached = self._repo.list_media()
            if cached:
                return cached + self._static_catalog

        return self._static_catalog

    def _fetch_from_omdb(self, intent: UserIntent, selected_media_type: str) -> list[MediaItem]:
        media_type = selected_media_type.lower() if selected_media_type != "Any" else "any"
        seen: set[str] = set()
        results: list[MediaItem] = []

        def _add(items: list) -> None:
            for item in items:
                if item.id not in seen:
                    seen.add(item.id)
                    results.append(item)

        # 1. Direct search with English raw words (catches specific shows like Breaking Bad)
        raw_words = [w.strip(",.!?") for w in intent.raw_text.split()
                     if len(w) > 3 and w.strip(",.!?").isascii()]
        if raw_words:
            _add(self._omdb.search(" ".join(raw_words[:4]), media_type=media_type))

        # 2. similar_to title search (e.g. "Breaking Bad gibi" → search "Breaking Bad")
        if intent.similar_to and not results:
            _add(self._omdb.search(intent.similar_to, media_type=media_type))

        # 3. Genre-based seed search
        if intent.genres:
            for genre in intent.genres[:3]:
                _add(self._omdb.search_by_genre(genre, media_type=media_type))

        if results:
            return results

        # 4. Final fallback
        _add(self._omdb.search("popular", media_type=media_type))
        return results

    def _fetch_from_spotify(self, intent: UserIntent) -> list[MediaItem]:
        if intent.moods:
            return self._spotify.search_by_mood(intent.moods[0])
        return self._spotify.search(intent.raw_text)

    def _fetch_from_tmdb(self, intent: UserIntent, selected_media_type: str) -> list[MediaItem]:
        media_type = selected_media_type.lower() if selected_media_type != "Any" else "any"
        seen: set[str] = set()
        results: list[MediaItem] = []

        similar_lower = (intent.similar_to or "").lower()

        def _add(items: list) -> None:
            for item in items:
                if item.id in seen:
                    continue
                if item.rating is not None and item.rating < 6.5:
                    continue
                # Skip making-of / behind-the-scenes when doing similar_to search
                if similar_lower and similar_lower in item.title.lower() and item.media_type == "movie":
                    continue
                seen.add(item.id)
                results.append(item)

        min_rating = 5.5 if intent.language else 6.5

        def _add_tmdb(items: list) -> None:
            for item in items:
                if item.id in seen:
                    continue
                if item.rating is not None and item.rating < min_rating:
                    continue
                if (item.popularity or 0) < 0.01:
                    continue
                if similar_lower and similar_lower in item.title.lower() and item.media_type == "movie":
                    continue
                seen.add(item.id)
                results.append(item)

        # 1. similar_to title search first
        if intent.similar_to:
            _add_tmdb(self._tmdb.search(intent.similar_to, media_type=media_type))

        # 2. Genre discover — best quality for genre queries
        year_from = year_to = None
        if intent.era:
            try:
                decade = int(intent.era.rstrip("s"))
                year_from, year_to = decade, decade + 9
            except ValueError:
                pass
        lang = intent.language or None
        if intent.genres:
            for genre in intent.genres[:3]:
                if media_type in ("series", "any"):
                    _add_tmdb(self._tmdb.discover_by_genre(genre, "tv", year_from=year_from, year_to=year_to, language=lang))
                if media_type in ("movie", "any"):
                    _add_tmdb(self._tmdb.discover_by_genre(genre, "movie", year_from=year_from, year_to=year_to, language=lang))
        elif lang:
            # Language-only query: no genre specified, fetch popular content in that language
            for mt in (["tv", "movie"] if media_type == "any" else (["tv"] if media_type == "series" else ["movie"])):
                for genre in ["comedy", "drama", "action"]:
                    _add_tmdb(self._tmdb.discover_by_genre(genre, mt, language=lang))

        # 3. Raw text search as fallback
        if not results:
            raw_words = [w.strip(",.!?") for w in intent.raw_text.split()
                         if len(w) > 3 and w.strip(",.!?").isascii()]
            query = " ".join(raw_words[:4]) if raw_words else intent.similar_to or ""
            if query:
                _add_tmdb(self._tmdb.search(query, media_type=media_type))

        return results[:20]

    def _filter_by_media_type(self, catalog: list[MediaItem], selected_media_type: str) -> list[MediaItem]:
        if selected_media_type == "Any":
            return catalog
        return [item for item in catalog if item.media_type == selected_media_type.lower()]
