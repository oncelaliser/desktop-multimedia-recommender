from __future__ import annotations

import json
import logging
import re

import requests

from core.chatbot.intent_parser import IntentParser, UserIntent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an intent extractor for a multimedia recommendation app.
Given a user query (may be in Turkish or English), extract a JSON object with these fields:

- media_type: one of "movie", "series", "music", "game", or null
- genres: list of zero or more from: crime, mystery, drama, comedy, sci-fi, horror, action,
  racing, sports, fantasy, romance, animation, documentary, chill, strategy
- moods: list of zero or more from: dark, calm, nostalgic, energetic, surreal
- era: decade string like "1990s", "1980s", or null
- similar_to: title of a specific movie/show/game the user wants something similar to, or null
- language: one of "tr", "ko", "ja", "es", "fr", "it", or null (only if user explicitly requests
  content in that language/country)

Rules:
- "gibi" or "tarzı" after a title = similar_to that title
- "türk"/"yerli" = language "tr"; "kore"/"k-drama" = "ko"; "japon"/"anime" = "ja"
- "anime" = both animation genre + language "ja"
- Return ONLY valid JSON. No explanation.

Examples:
User: "breaking bad gibi bir dizi"
{"media_type":"series","genres":["crime","drama"],"moods":["dark"],"era":null,"similar_to":"Breaking Bad","language":null}

User: "90'larda geçen nostaljik türk komedi filmi"
{"media_type":"movie","genres":["comedy"],"moods":["nostalgic"],"era":"1990s","similar_to":null,"language":"tr"}

User: "yarış arabası oyunu"
{"media_type":"game","genres":["racing","action"],"moods":["energetic"],"era":null,"similar_to":null,"language":null}

User: "kasvetli ama düşündürücü bir şey"
{"media_type":null,"genres":["drama"],"moods":["dark"],"era":null,"similar_to":null,"language":null}
"""


class LLMIntentParser:
    """LLM-powered intent parser. Falls back to keyword parser on any failure."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        model: str,
        fallback: IntentParser | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._fallback = fallback or IntentParser()

    def parse(self, text: str) -> UserIntent:
        try:
            return self._parse_with_llm(text)
        except Exception as exc:
            logger.warning("LLM intent parse failed, using keyword fallback: %s", exc)
            return self._fallback.parse(text)

    def _parse_with_llm(self, text: str) -> UserIntent:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.0,
            "max_tokens": 256,
        }
        resp = requests.post(
            f"{self._base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if present
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()
        data = json.loads(content)

        valid_genres = {
            "crime", "mystery", "drama", "comedy", "sci-fi", "horror", "action",
            "racing", "sports", "fantasy", "romance", "animation", "documentary",
            "chill", "strategy",
        }
        valid_moods = {"dark", "calm", "nostalgic", "energetic", "surreal"}
        valid_media = {"movie", "series", "music", "game"}
        valid_lang = {"tr", "ko", "ja", "es", "fr", "it"}

        genres = [g for g in (data.get("genres") or []) if g in valid_genres]
        moods = [m for m in (data.get("moods") or []) if m in valid_moods]
        media_type = data.get("media_type") if data.get("media_type") in valid_media else None
        language = data.get("language") if data.get("language") in valid_lang else None
        era = data.get("era") if isinstance(data.get("era"), str) else None
        similar_to = data.get("similar_to") if isinstance(data.get("similar_to"), str) else None

        return UserIntent(
            raw_text=text,
            media_type=media_type,
            genres=genres,
            moods=moods,
            era=era,
            similar_to=similar_to,
            language=language,
        )
