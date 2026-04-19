from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserPrompt:
    text: str
    preferred_media_type: str | None = None
