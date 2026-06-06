from __future__ import annotations

import random

from core.chatbot.intent_parser import UserIntent

_GREETINGS = [
    "Selam! Film, dizi, müzik veya oyun önerebilirim. Ne arıyorsun?",
    "Merhaba! Ruh haline göre bir şeyler bulalım. Ne tür içerik istiyorsun?",
    "Hey! Bugün ne izlemek ya da dinlemek istiyorsun?",
]

_FALLBACKS = [
    "Seni duydum, şimdi en uygun önerileri sıralıyorum.",
    "Tamam, bakalım ne bulabiliriz.",
    "Anladım, şimdi önerileri hazırlıyorum.",
]

_TYPE_LABELS = {
    "movie": "film",
    "series": "dizi",
    "music": "müzik",
    "game": "oyun",
}

_GENRE_LABELS = {
    "crime": "suç/polisiye",
    "drama": "drama",
    "comedy": "komedi",
    "horror": "korku",
    "sci-fi": "bilim kurgu",
    "action": "aksiyon",
    "mystery": "gizem",
    "romance": "romantik",
    "thriller": "gerilim",
    "animation": "animasyon",
    "documentary": "belgesel",
    "chill": "sakinletici",
    "fantasy": "fantastik/fantasy",
}

_MOOD_LABELS = {
    "dark": "karanlık",
    "calm": "sakin",
    "nostalgic": "nostaljik",
    "energetic": "enerjik",
    "surreal": "tuhaf/sürrealist",
}


def greeting_response() -> str:
    return random.choice(_GREETINGS)


def recommendation_intro(intent: UserIntent) -> str:
    parts: list[str] = []

    if intent.similar_to:
        parts.append(f"**{intent.similar_to}** tarzı")

    if intent.media_type:
        parts.append(_TYPE_LABELS.get(intent.media_type, intent.media_type))

    if intent.genres:
        genre_str = ", ".join(_GENRE_LABELS.get(g, g) for g in intent.genres[:2])
        parts.append(genre_str)

    if intent.moods:
        mood_str = " ve ".join(_MOOD_LABELS.get(m, m) for m in intent.moods[:2])
        parts.append(mood_str + " atmosfer")

    if intent.era:
        parts.append(f"{intent.era} dönemi")

    if not parts:
        return random.choice(_FALLBACKS)

    intro = ", ".join(parts)
    return f"{intro.capitalize()} arıyorsun — işte öneriler:"
