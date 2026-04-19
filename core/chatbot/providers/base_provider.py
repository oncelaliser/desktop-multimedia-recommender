from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderResult:
    text: str
    provider_name: str
    is_fallback: bool = False


class BaseChatProvider(ABC):
    name: str

    @abstractmethod
    def generate_response(self, user_message: str, context: dict | None = None) -> ProviderResult:
        raise NotImplementedError
