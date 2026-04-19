from __future__ import annotations


class EmbeddingRepository:
    """Stores MiniLM vectors so they do not need to be recalculated."""

    def get_embedding(self, media_id: str, model_name: str) -> list[float] | None:
        raise NotImplementedError

    def save_embedding(self, media_id: str, model_name: str, embedding: list[float]) -> None:
        raise NotImplementedError
