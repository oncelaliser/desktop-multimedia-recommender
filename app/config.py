from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str
    lmstudio_base_url: str
    lmstudio_model: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
            lmstudio_base_url=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            lmstudio_model=os.getenv("LMSTUDIO_MODEL", "local-model"),
        )
