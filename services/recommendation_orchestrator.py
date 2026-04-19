from __future__ import annotations

from core.chatbot.chat_service import ChatService
from core.recommendation.recommender_service import RecommenderService


class RecommendationOrchestrator:
    """Application service boundary for future UI simplification."""

    def __init__(self, chat_service: ChatService, recommender_service: RecommenderService) -> None:
        self.chat_service = chat_service
        self.recommender_service = recommender_service
