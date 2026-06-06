from __future__ import annotations

import re
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
    language: str | None = None


class IntentParser:
    """Small deterministic parser used until an LLM provider is connected."""

    MEDIA_KEYWORDS = {
        "movie": ("film", "movie", "sinema"),
        "series": ("dizi", "series", "show"),
        "music": ("müzik", "music", "song", "şarkı", "playlist"),
        "game": ("oyun", "game"),
    }

    GENRE_KEYWORDS = {
        "crime": ("suç", "crime", "detective", "dedektif", "narkotik", "cinayet",
                  "narcotic", "drug", "drugs", "murder", "killer", "mafia", "mob",
                  "heist", "uyuşturucu", "katil"),
        "mystery": ("gizem", "mystery", "mysterious", "gizemli", "paranormal"),
        "drama": ("dram", "drama", "duygusal", "dramatik"),
        "comedy": ("komedi", "comedy", "funny", "güldürü", "komik", "eğlenceli", "neşeli", "gülünç"),
        "sci-fi": ("bilim kurgu", "sci-fi", "science fiction", "cyberpunk", "uzay", "fütürist",
                   "space", "robot", "alien", "future", "distopik", "distopia", "dystopia"),
        "horror": ("korku", "horror", "gerilim", "thriller", "scary", "haunted", "ürkütücü", "kabus"),
        "action": ("aksiyon", "action", "macera", "adventure", "fight", "war", "savaş", "dövüş"),
        "fantasy": ("fantastik", "fantastic", "fantasy", "ejderha", "dragon", "büyü", "magic",
                    "sihir", "orta çağ", "medieval", "kılıç", "sword", "wizard", "büyücü",
                    "taht", "throne", "elf", "goblin", "myth", "mitoloji", "efsane",
                    "kingdom", "krallık", "şövalye", "knight", "intrika", "entrika"),
        "romance": ("romantik", "romance", "aşk", "sevgi", "ask", "love story"),
        "animation": ("animasyon", "animation", "anime", "çizgi"),
        "documentary": ("belgesel", "documentary"),
        "chill": ("sakin", "chill", "relax", "rahatlatıcı", "feel good"),
    }

    MOOD_KEYWORDS = {
        "dark": ("karanlık", "dark", "kasvetli", "ağır"),
        "calm": ("sakin", "calm", "soft", "rahat", "huzurlu"),
        "nostalgic": ("nostaljik", "nostalgic", "90'lar", "80'ler"),
        "energetic": ("enerjik", "energetic", "hızlı"),
        "surreal": ("tuhaf", "surreal", "garip", "absürt", "absürd", "absurd", "abzürt",
                    "saçma", "çılgın", "çılgınca", "geğirme", "geğirmeli", "sıçma", "sıçmalı"),
    }

    LANGUAGE_KEYWORDS = {
        "tr": ("türk", "türkçe", "yerli", "turkish", "turkey", "anadolu"),
        "ko": ("kore", "korean", "kdrama", "k-drama"),
        "ja": ("japon", "japanese", "japan"),
        "es": ("ispanyol", "spanish", "spain"),
        "fr": ("fransız", "french", "france"),
        "it": ("italyan", "italian", "italy"),
    }

    def parse(self, text: str) -> UserIntent:
        normalized = normalize_text(text)
        media_type = self._first_match(normalized, self.MEDIA_KEYWORDS)
        genres = self._all_matches(normalized, self.GENRE_KEYWORDS)
        moods = self._all_matches(normalized, self.MOOD_KEYWORDS)
        era = self._extract_era(normalized)
        similar_to = self._extract_similar_to(text)
        language = self._first_match(normalized, self.LANGUAGE_KEYWORDS)

        return UserIntent(
            raw_text=text,
            media_type=media_type,
            genres=genres,
            moods=moods,
            era=era,
            similar_to=similar_to,
            language=language,
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
        # Match "1970s", "70s", "70'lar", "70'ler", "1970", etc.
        m = re.search(r"\b(19[4-9]\d|20[012]\d)s?\b", text)
        if m:
            year = int(m.group(1))
            return f"{(year // 10) * 10}s"
        m = re.search(r"\b([4-9]\d)[''']?(lar|ler|s)?\b", text)
        if m:
            decade = int(m.group(1))
            if 40 <= decade <= 99:
                return f"19{decade}s"
        return None

    def _extract_similar_to(self, text: str) -> str | None:
        # "X gibi", "X tarzı", "like X", "similar to X"
        lowered = text.lower()

        # Before-marker patterns: "Breaking Bad gibi", "Twin Peaks tarzı"
        before_markers = ("tarzı", "gibi")
        for marker in before_markers:
            if marker in lowered:
                idx = lowered.index(marker)
                before = text[:idx].strip().rstrip(",.")
                words = before.split()
                if words:
                    # take up to last 4 words (handles multi-word titles)
                    return " ".join(words[-4:])

        # After-marker patterns: "like Breaking Bad", "similar to The Wire"
        after_patterns = (r"like\s+(.+?)(?:\s+(?:gibi|tarzı|series|dizi|film|movie)|$)",
                          r"similar to\s+(.+?)(?:\s+(?:series|dizi|film|movie)|$)")
        for pattern in after_patterns:
            m = re.search(pattern, lowered)
            if m:
                candidate = m.group(1).strip().title()
                if candidate:
                    return candidate
        return None
