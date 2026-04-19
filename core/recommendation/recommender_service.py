from __future__ import annotations

from core.chatbot.intent_parser import IntentParser
from core.recommendation.explanation_builder import ExplanationBuilder
from core.recommendation.sample_catalog import SAMPLE_MEDIA
from core.recommendation.scoring_engine import ScoringEngine
from data.models.media_item import MediaItem
from data.models.recommendation import Recommendation


class RecommenderService:
    def __init__(
        self,
        catalog: list[MediaItem] | None = None,
        intent_parser: IntentParser | None = None,
        scoring_engine: ScoringEngine | None = None,
        explanation_builder: ExplanationBuilder | None = None,
    ) -> None:
        self.catalog = catalog or SAMPLE_MEDIA
        self.intent_parser = intent_parser or IntentParser()
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.explanation_builder = explanation_builder or ExplanationBuilder()

    def recommend(
        self,
        user_prompt: str,
        selected_media_type: str = "Any",
        limit: int = 5,
    ) -> list[Recommendation]:
        intent = self.intent_parser.parse(user_prompt)
        catalog = self._filter_by_media_type(self.catalog, selected_media_type)
        scored = [
            Recommendation(
                media=media,
                score=self.scoring_engine.score(intent, media),
                reason=self.explanation_builder.build(intent, media),
            )
            for media in catalog
        ]
        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

    def _filter_by_media_type(self, catalog: list[MediaItem], selected_media_type: str) -> list[MediaItem]:
        if selected_media_type == "Any":
            return catalog
        return [item for item in catalog if item.media_type == selected_media_type.lower()]
