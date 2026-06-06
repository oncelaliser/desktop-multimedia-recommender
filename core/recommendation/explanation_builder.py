from __future__ import annotations

from core.chatbot.intent_parser import UserIntent
from data.models.media_item import MediaItem

_GENRE_TR = {
    "crime": "suç/polisiye", "drama": "dram", "comedy": "komedi",
    "horror": "korku", "sci-fi": "bilim kurgu", "action": "aksiyon",
    "mystery": "gizem", "romance": "romantik", "thriller": "gerilim",
    "animation": "animasyon", "documentary": "belgesel", "chill": "sakinletici",
    "fantasy": "fantastik/fantasy",
    "racing": "yarış/motorsport",
    "sports": "spor",
}

_MOOD_TR = {
    "dark": "karanlık", "calm": "sakin", "nostalgic": "nostaljik",
    "energetic": "enerjik", "surreal": "sürrealist",
}

_TYPE_TR = {
    "movie": "film", "series": "dizi", "music": "müzik", "game": "oyun",
}


class ExplanationBuilder:
    def build(self, intent: UserIntent, media: MediaItem) -> str:
        reasons: list[str] = []
        matched_genres = sorted(set(intent.genres) & set(media.genres))
        matched_moods = sorted(set(intent.moods) & set(media.moods))

        if intent.similar_to:
            reasons.append(f"{intent.similar_to} tarzına benzer yapıda")

        if matched_genres:
            genre_labels = [_GENRE_TR.get(g, g) for g in matched_genres[:2]]
            reasons.append(f"{', '.join(genre_labels)} türünde")

        if matched_moods:
            mood_labels = [_MOOD_TR.get(m, m) for m in matched_moods[:2]]
            reasons.append(f"{' ve '.join(mood_labels)} atmosferi var")

        if intent.era and media.release_year:
            try:
                decade = int(intent.era.rstrip("s"))
                if decade <= media.release_year <= decade + 9:
                    reasons.append(f"{intent.era} döneminden")
                elif abs(media.release_year - decade) <= 14:
                    reasons.append(f"{intent.era} dönemine yakın ({media.release_year})")
            except ValueError:
                pass

        if intent.media_type and intent.media_type == media.media_type and not reasons:
            reasons.append(f"aradığın {_TYPE_TR.get(media.media_type, media.media_type)} türünde")

        if media.rating and media.rating >= 8.0:
            reasons.append(f"IMDb puanı yüksek (★{media.rating:.1f})")

        if not reasons:
            return "İçerik açıklaması isteğinle örtüşüyor."

        return "; ".join(reasons).capitalize() + "."
