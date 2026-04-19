from __future__ import annotations

from app.config import AppConfig
from common.exceptions import ProviderError
from core.chatbot.providers.base_provider import BaseChatProvider, ProviderResult
from core.chatbot.providers.lmstudio_provider import LMStudioProvider
from core.chatbot.providers.offline_template_provider import OfflineTemplateProvider
from core.chatbot.providers.openai_compatible_provider import OpenAICompatibleProvider


class ChatService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.offline_provider = OfflineTemplateProvider()

    def provider_for_mode(self, mode: str) -> BaseChatProvider:
        if mode == "OpenAI-Compatible API":
            return OpenAICompatibleProvider(
                base_url=self.config.openai_base_url,
                api_key=self.config.openai_api_key,
                model=self.config.openai_model,
            )
        if mode == "LM Studio Local":
            return LMStudioProvider(
                base_url=self.config.lmstudio_base_url,
                model=self.config.lmstudio_model,
            )
        return self.offline_provider

    def respond(self, user_message: str, mode: str, context: dict | None = None) -> ProviderResult:
        provider = self.provider_for_mode(mode)
        try:
            return provider.generate_response(user_message, context=context)
        except ProviderError as exc:
            fallback = self.offline_provider.generate_response(user_message, context=context)
            return ProviderResult(
                text=f"{fallback.text}\n\nNot: {mode} yanıt veremedi, offline moda geçildi. ({exc})",
                provider_name=fallback.provider_name,
                is_fallback=True,
            )
        except Exception as exc:
            fallback = self.offline_provider.generate_response(user_message, context=context)
            return ProviderResult(
                text=f"{fallback.text}\n\nNot: {mode} sırasında hata oluştu, offline moda geçildi. ({exc})",
                provider_name=fallback.provider_name,
                is_fallback=True,
            )
