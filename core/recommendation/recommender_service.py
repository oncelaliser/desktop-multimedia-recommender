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
        parsed_intent: UserIntent | None = None,
    ) -> list[Recommendation]:
        intent = parsed_intent if parsed_intent is not None else self.intent_parser.parse(user_prompt)
        catalog = self._build_catalog(intent, selected_media_type)

        # If similar_to is set and TMDB found a match, infer media_type from it
        # so "breaking bad gibi" (Any) doesn't return games alongside shows.
        # Only infer when the user hasn't specified a type AND intent has no type either.
        effective_media_type = selected_media_type
        if (intent.similar_to and self._tmdb
                and selected_media_type == "Any"
                and intent.media_type is None):
            found = self._tmdb.find_by_title(intent.similar_to, "any")
            if found:
                _, kind = found
                effective_media_type = "series" if kind == "tv" else "movie"

        catalog = self._filter_by_media_type(catalog, effective_media_type)

        # In "Any" mode, hide games/music unless the user explicitly asked for them.
        # Games dominate by rating but users saying "kasvetli bir şey" expect movies/series.
        _GAME_GENRES = {"racing", "strategy", "sports"}
        if effective_media_type == "Any":
            wants_game = (
                intent.media_type == "game"
                or bool(set(intent.genres) & _GAME_GENRES)
            )
            wants_music = intent.media_type == "music"
            if not wants_game:
                catalog = [m for m in catalog if m.media_type != "game"]
            if not wants_music:
                catalog = [m for m in catalog if m.media_type != "music"]

        # Tiered, provenance-based boost. The LLM already did the hard semantic work
        # (mapping "türk WWI film" → Çanakkale 1915); a crude TF-IDF re-score must NOT
        # demote those curated picks below famous sample items. So we rank by how strongly
        # the pick is vouched for:
        #   seed       (a title the LLM named)        → strongest
        #   seed_rec   (TMDB's similar/recs to a seed)→ strong
        #   discover   (generic genre/language match) → mild
        #   sample     (static catalog)               → none
        has_seeds = bool(intent.similar_to or getattr(intent, "seed_titles", []))
        live_ids = {m.id for m in catalog if m.source != "sample"}
        provenance = getattr(self, "_provenance", {}) or {}
        _TIER_BOOST = {"seed": 40.0, "seed_rec": 25.0, "discover": 8.0}

        def _boost_for(media: MediaItem) -> float:
            if media.source == "sample":
                return 0.0
            if not has_seeds:
                return 0.0
            tier = provenance.get(media.id, "discover")
            return _TIER_BOOST.get(tier, 8.0)

        # Deduplicate by normalized title+type across sources (prefer higher-scored)
        seen_titles: dict[str, Recommendation] = {}
        for media in catalog:
            key = f"{media.title.lower().strip()}|{media.media_type}"
            base_score = self.scoring_engine.score(intent, media)
            rec = Recommendation(
                media=media,
                score=min(round(base_score + _boost_for(media), 1), 99.9),
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
        # Provenance: how strongly the LLM/TMDB vouches for each item id.
        # "seed" = a title the LLM named, "seed_rec" = TMDB's similar/recs to a seed,
        # "discover" = generic genre/language discovery. Used for tiered ranking later.
        provenance: dict[str, str] = {}
        self._provenance = provenance

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

        def _add_tmdb(items: list, enforce_language: bool = False, tier: str = "discover") -> None:
            for item in items:
                if item.id in seen:
                    continue
                # Seed titles were explicitly named by the LLM — don't filter them on
                # rating/popularity (niche films like "Çanakkale 1915" have low TMDB
                # popularity but are exactly what the user asked for).
                is_seed = tier == "seed"
                if not is_seed and item.rating is not None and item.rating < min_rating:
                    continue
                if not is_seed and (item.popularity or 0) < 0.01:
                    continue
                if similar_lower and similar_lower in item.title.lower() and item.media_type == "movie":
                    continue
                # When the user asked for a specific language, drop off-language items
                # (e.g. "türk savaş filmi" → skip War Horse that a Turkish seed recommends).
                if (enforce_language and intent.language
                        and item.language and item.language != intent.language):
                    continue
                # Recency / year-range is a hard constraint — applies even to seeds
                # (e.g. "son 5 yıl" must not surface The Matrix from 1999).
                if intent.year_min and item.release_year and item.release_year < intent.year_min:
                    continue
                if intent.year_max and item.release_year and item.release_year > intent.year_max:
                    continue
                seen.add(item.id)
                results.append(item)
                provenance[item.id] = tier

        # Keyword-based discovery for specific subgenres TMDB can't find via genre alone
        _KEYWORD_MAP = {
            "yarış":    "10039|302340|268011|266725",  # racing, auto racing, motor racing, street racing
            "sürüş":   "10039|302340|266725",
            "formula":  "10039|302340",
            "araba":    "10039|302340|266725",
            "hızlı":   "10039|266725",
            "futbol":   "13042|352822|579",     # football/soccer, american football
            "basketbol":"169055",                # NBA/basketball
            "boks":     "209476",               # boxing
            "güreş":    "11451",                # wrestling
            "belgesel": None,                    # handled by genre
        }
        raw_lower = intent.raw_text.lower()
        for tr_word, kw_ids in _KEYWORD_MAP.items():
            if tr_word in raw_lower and kw_ids:
                for item in self._tmdb.discover_by_keywords(kw_ids, "movie") + self._tmdb.discover_by_keywords(kw_ids, "tv"):
                    # Tag with the matched subgenre so scoring picks it up
                    if tr_word in ("yarış", "sürüş", "formula") and "racing" not in item.genres:
                        from dataclasses import replace
                        item = replace(item, genres=item.genres + ["racing"])
                    elif tr_word in ("futbol", "basketbol", "boks", "güreş") and "sports" not in item.genres:
                        from dataclasses import replace
                        item = replace(item, genres=item.genres + ["sports"])
                    _add_tmdb([item])

        # 1a. similar_to: use TMDB's own similar/recommendations endpoints (much better signal)
        if intent.similar_to:
            for mt in (["movie", "tv"] if media_type == "any"
                       else (["tv"] if media_type == "series" else ["movie"])):
                found = self._tmdb.find_by_title(intent.similar_to, mt)
                if found:
                    tmdb_id, kind = found
                    _add_tmdb(self._tmdb.recommendations(tmdb_id, kind), tier="seed_rec")
                    _add_tmdb(self._tmdb.similar(tmdb_id, kind), tier="seed_rec")
            # fallback: title search if no ID found
            if not results:
                _add_tmdb(self._tmdb.search(intent.similar_to, media_type=media_type), tier="seed_rec")

        # 1b. seed_titles: LLM-suggested representative titles → fetch their TMDB recommendations.
        # This bridges the semantic gap (e.g. "italyan mafya" → Godfather → similar films).
        # Use "any" so find_by_title picks the most-voted version (TV vs movie) automatically.
        # Balance across seeds: add the seed ITSELF + a capped number of its recommendations,
        # so one seed (e.g. Star Wars) doesn't crowd out the others (e.g. Interstellar).
        seed_titles = getattr(intent, "seed_titles", []) or []
        # More seeds → richer coverage (e.g. several Yeşilçam classics), but cap recs per
        # seed lower so total API calls and result count stay bounded.
        per_seed_cap = 4
        for seed in seed_titles[:5]:
            if seed == intent.similar_to:
                continue  # already handled above
            # "any" uses vote_count to pick the most famous match (e.g. Peaky Blinders TV, not the 2023 film)
            search_mt = "any" if media_type == "any" else ("tv" if media_type == "series" else "movie")
            found = self._tmdb.find_by_title(seed, search_mt)
            if not found:
                continue
            tmdb_id, kind = found
            # add the seed itself so famous titles the user implied actually show up
            seed_item = self._tmdb.details(tmdb_id, kind)
            if seed_item:
                _add_tmdb([seed_item], enforce_language=True, tier="seed")
            # add a capped slice of this seed's recommendations (round-robin fairness),
            # honoring the requested language so off-language recs don't leak in
            recs = self._tmdb.recommendations(tmdb_id, kind) + self._tmdb.similar(tmdb_id, kind)
            before = len(results)
            for item in recs:
                if len(results) - before >= per_seed_cap:
                    break
                _add_tmdb([item], enforce_language=True, tier="seed_rec")

        # 2. Genre discover — best quality for genre queries
        year_from = year_to = None
        if intent.era:
            try:
                decade = int(intent.era.rstrip("s"))
                year_from, year_to = decade, decade + 9
            except ValueError:
                pass
        # Explicit year bounds ("son 5 yıl", "2010 sonrası") override / refine the decade.
        if intent.year_min:
            year_from = intent.year_min
        if intent.year_max:
            year_to = intent.year_max
        # discover_by_genre only filters when BOTH bounds are set; fill the open side
        # so one-sided ranges ("son 5 yıl" → from=2021) still filter server-side.
        if year_from and not year_to:
            from datetime import date
            year_to = date.today().year
        if year_to and not year_from:
            year_from = 1900
        lang = intent.language or None
        # When seeds produced a solid set of curated results, genre discover is only filler —
        # don't let generic genre matches (e.g. any war drama) crowd out the seed-based picks.
        seeds_satisfied = len(results) >= 8
        if intent.genres and not seeds_satisfied:
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
