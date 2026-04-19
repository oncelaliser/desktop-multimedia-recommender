from __future__ import annotations

from common.utils import normalize_text
from core.chatbot.intent_parser import IntentParser
from core.chatbot.prompt_templates import greeting_response, recommendation_intro
from core.chatbot.providers.base_provider import BaseChatProvider, ProviderResult


class OfflineTemplateProvider(BaseChatProvider):
    name = "Offline Basic"

    def __init__(self, intent_parser: IntentParser | None = None) -> None:
        self.intent_parser = intent_parser or IntentParser()

    def generate_response(self, user_message: str, context: dict | None = None) -> ProviderResult:
        normalized = normalize_text(user_message)
        if normalized in {"selam", "merhaba", "hi", "hello"} or "nasılsın" in normalized:
            return ProviderResult(text=greeting_response(), provider_name=self.name)

        intent = self.intent_parser.parse(user_message)
        return ProviderResult(text=recommendation_intro(intent), provider_name=self.name)
