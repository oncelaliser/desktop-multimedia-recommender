from __future__ import annotations

from core.chatbot.intent_parser import UserIntent
from data.models.media_item import MediaItem


class ExplanationBuilder:
    def build(self, intent: UserIntent, media: MediaItem) -> str:
        reasons: list[str] = []
        matched_genres = sorted(set(intent.genres) & set(media.genres))
        matched_moods = sorted(set(intent.moods) & set(media.moods))

        if intent.media_type and intent.media_type == media.media_type:
            reasons.append(f"{media.media_type} isteğinle eşleşiyor")
        if matched_genres:
            reasons.append(f"tür olarak {', '.join(matched_genres)} sinyallerini yakalıyor")
        if matched_moods:
            reasons.append(f"atmosfer olarak {', '.join(matched_moods)} tarafına yakın")
        if intent.era == "1990s" and media.release_year and 1990 <= media.release_year <= 1999:
            reasons.append("90'lar dönemine uyuyor")

        if not reasons:
            return "Açıklama ve etiketleri kullanıcı isteğine anlamsal olarak yakın görünüyor."

        return "; ".join(reasons).capitalize() + "."
