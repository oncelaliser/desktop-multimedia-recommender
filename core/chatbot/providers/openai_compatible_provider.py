from __future__ import annotations

import requests

from common.exceptions import ProviderError
from core.chatbot.providers.base_provider import BaseChatProvider, ProviderResult


class OpenAICompatibleProvider(BaseChatProvider):
    """Provider for OpenAI-compatible chat completion APIs."""

    name = "OpenAI-Compatible API"

    def __init__(self, base_url: str, api_key: str | None, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def generate_response(self, user_message: str, context: dict | None = None) -> ProviderResult:
        if not self.api_key:
            raise ProviderError("API key is not configured.")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a concise multimedia recommendation assistant. "
                        "Help interpret the user's media taste, but do not invent final "
                        "recommendations outside the application's candidate list."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.4,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=20,
        )
        if response.status_code >= 400:
            raise ProviderError(f"Provider returned HTTP {response.status_code}.")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return ProviderResult(text=content.strip(), provider_name=self.name)
