from __future__ import annotations

from dataclasses import dataclass, field

from common.utils import normalize_text


@dataclass(frozen=True)
class UserIntent:
    raw_text: str
    media_type: str | None = None
    genres: list[str] = field(default_factory=list)
    moods: list[str] = field(default_factory=list)
    era: str | None = None
    similar_to: str | None = None


class IntentParser:
    """Small deterministic parser used until an LLM provider is connected."""

    MEDIA_KEYWORDS = {
        "movie": ("film", "movie", "sinema"),
        "series": ("dizi", "series", "show"),
        "music": ("müzik", "music", "song", "şarkı", "playlist"),
        "game": ("oyun", "game"),
    }

    GENRE_KEYWORDS = {
        "crime": ("suç", "crime", "detective", "dedektif"),
        "mystery": ("gizem", "mystery", "mysterious"),
        "drama": ("dram", "drama"),
        "comedy": ("komedi", "comedy", "funny"),
        "sci-fi": ("bilim kurgu", "sci-fi", "science fiction", "cyberpunk"),
        "horror": ("korku", "horror"),
        "action": ("aksiyon", "action"),
        "chill": ("sakin", "chill", "relax", "rahatlatıcı"),
    }

    MOOD_KEYWORDS = {
        "dark": ("karanlık", "dark", "kasvetli"),
        "calm": ("sakin", "calm", "soft", "rahat"),
        "nostalgic": ("nostaljik", "nostalgic", "90'lar", "80'ler"),
        "energetic": ("enerjik", "energetic", "hızlı"),
        "surreal": ("tuhaf", "surreal", "garip"),
    }

    def parse(self, text: str) -> UserIntent:
        normalized = normalize_text(text)
        media_type = self._first_match(normalized, self.MEDIA_KEYWORDS)
        genres = self._all_matches(normalized, self.GENRE_KEYWORDS)
        moods = self._all_matches(normalized, self.MOOD_KEYWORDS)
        era = self._extract_era(normalized)
        similar_to = self._extract_similar_to(text)

        return UserIntent(
            raw_text=text,
            media_type=media_type,
            genres=genres,
            moods=moods,
            era=era,
            similar_to=similar_to,
        )

    def _first_match(self, text: str, dictionary: dict[str, tuple[str, ...]]) -> str | None:
        matches = self._all_matches(text, dictionary)
        return matches[0] if matches else None

    def _all_matches(self, text: str, dictionary: dict[str, tuple[str, ...]]) -> list[str]:
        found: list[str] = []
        for label, keywords in dictionary.items():
            if any(keyword in text for keyword in keywords):
                found.append(label)
        return found

    def _extract_era(self, text: str) -> str | None:
        if "90" in text or "1990" in text:
            return "1990s"
        if "80" in text or "1980" in text:
            return "1980s"
        if "2000" in text:
            return "2000s"
        return None

    def _extract_similar_to(self, text: str) -> str | None:
        markers = ("tarzı", "gibi", "like")
        lowered = text.lower()
        for marker in markers:
            if marker in lowered:
                before_marker = text[: lowered.index(marker)].strip()
                words = before_marker.split()
                if words:
                    return " ".join(words[-3:])
        return None
