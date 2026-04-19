from __future__ import annotations

from core.chatbot.providers.openai_compatible_provider import OpenAICompatibleProvider


class LMStudioProvider(OpenAICompatibleProvider):
    """LM Studio exposes an OpenAI-compatible local server."""

    name = "LM Studio Local"

    def __init__(self, base_url: str, model: str) -> None:
        super().__init__(base_url=base_url, api_key="lm-studio", model=model)
