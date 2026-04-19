from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    created_at: datetime

    @classmethod
    def user(cls, content: str) -> "ChatMessage":
        return cls(role="user", content=content, created_at=datetime.now())

    @classmethod
    def assistant(cls, content: str) -> "ChatMessage":
        return cls(role="assistant", content=content, created_at=datetime.now())
