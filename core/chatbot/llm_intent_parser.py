from __future__ import annotations

import json
import logging
import re

import requests

from core.chatbot.intent_parser import IntentParser, UserIntent

logger = logging.getLogger(__name__)

_REPLY_FIELD = """\

The JSON MUST also include a "reply" field (REQUIRED, do not omit):
- reply: warm Turkish answer (2-4 sentences) recommending exactly the seed_titles by name, plain prose.
Example: {"reply":"Türk mafya dizileri için Çukur, Ezel ve Kurtlar Vadisi'ni öneririm; üçü de suç dünyasını çarpıcı işliyor.","media_type":"series","genres":["crime","drama"],"moods":["dark"],"era":null,"year_min":null,"year_max":null,"similar_to":null,"language":"tr","seed_titles":["Çukur","Ezel","Kurtlar Vadisi"]}"""

_SYSTEM_PROMPT = """\
Extract a JSON object from the user's movie/TV query (Turkish or English). Fields:
- media_type: "movie"|"series"|"music"|"game"|null
- genres: subset of [crime,mystery,drama,comedy,sci-fi,horror,action,racing,sports,fantasy,romance,animation,documentary,chill,strategy]
- moods: subset of [dark,calm,nostalgic,energetic,surreal]
- era: decade like "1990s" or null
- year_min/year_max: release-year bounds or null. Current year={CURRENT_YEAR}. "son 5 yıl"→year_min={CURRENT_YEAR}-5; "yeni/güncel"→year_min={CURRENT_YEAR}-3; "2010 sonrası"→year_min=2010; "2000 öncesi"→year_max=1999.
- similar_to: the title if user says "X gibi/tarzı/like X", else null
- language: "tr"|"ko"|"ja"|"es"|"fr"|"it"|"de"|"zh"|"hi"|"pt"|"sv"|null. Set ONLY when user names a country/nationality (türk,kore,alman,japon...). NOT just because the query is Turkish. Reflects content ORIGIN ("italyan mafya"→null, Godfather is American).
- seed_titles: 1-5 famous REAL titles best matching the request (the key field — use world knowledge). e.g. "italyan mafya"→["The Godfather","Goodfellas","Gomorrah"]; "alman bilim kurgu dizi"→["Dark","1899"]; "new mexico uyuşturucu"→["Breaking Bad","Better Call Saul"]; "yeşilçam komedi"→["Hababam Sınıfı","Tosun Paşa","Şabaniye"]. [] only if too vague. If user said "X gibi", exclude X but include similar.

Key distinctions:
- "bilim adamı/insanı/scientist" = films ABOUT scientists (biopics: A Beautiful Mind, The Imitation Game), NOT sci-fi.
- "bilim kurgu/sci-fi/uzay" = science-fiction genre.

Return ONLY valid JSON.

Example — "new mexico, aksiyon, uyuşturucu":
{"media_type":"series","genres":["crime","action"],"moods":["dark"],"era":null,"year_min":null,"year_max":null,"similar_to":null,"language":null,"seed_titles":["Breaking Bad","Better Call Saul","Narcos"]}"""


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
            _, intent = self._call_llm(text, want_reply=False)
            return intent
        except Exception as exc:
            logger.warning("LLM intent parse failed, using keyword fallback: %s", exc)
            return self._fallback.parse(text)

    def analyze(self, text: str) -> tuple[str | None, UserIntent]:
        """Single LLM call returning both a conversational reply and the structured intent.
        This keeps the chatbot answer and the recommendation panel perfectly in sync and
        halves API usage (one call instead of separate chat + intent calls).
        On failure, returns (None, keyword-fallback intent) so the caller can degrade gracefully."""
        try:
            return self._call_llm(text, want_reply=True)
        except Exception as exc:
            logger.warning("LLM analyze failed, using keyword fallback: %s", exc)
            return None, self._fallback.parse(text)

    @staticmethod
    def _extract_json(content: str) -> dict:
        """Extract the first balanced JSON object, ignoring any trailing prose
        the model may append (which would otherwise break json.loads)."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        # Find the first '{' and scan for its matching '}'
        start = content.find("{")
        if start == -1:
            raise ValueError("no JSON object in LLM response")
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(content)):
            ch = content[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return json.loads(content[start:i + 1])
        raise ValueError("unbalanced JSON object in LLM response")

    def _call_llm(self, text: str, want_reply: bool) -> tuple[str | None, UserIntent]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        from datetime import date
        base_prompt = (_SYSTEM_PROMPT + _REPLY_FIELD) if want_reply else _SYSTEM_PROMPT
        system_prompt = base_prompt.replace("{CURRENT_YEAR}", str(date.today().year))
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.3 if want_reply else 0.0,
            # Force valid JSON output (Groq/OpenAI JSON mode) so the whole response is one
            # object — prevents the model from emitting prose instead of/around the JSON.
            "response_format": {"type": "json_object"},
        }
        # Retry on 429 (rate limit) with short backoff — Groq's free tier throttles by
        # tokens/minute, and a brief wait usually clears it without losing the request.
        import time
        resp = None
        for attempt in range(3):
            resp = requests.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 429 and attempt < 2:
                retry_after = resp.headers.get("retry-after")
                wait = float(retry_after) if retry_after else (1.5 * (attempt + 1))
                time.sleep(min(wait, 6.0))
                continue
            break
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if present
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()
        data = self._extract_json(content)

        valid_genres = {
            "crime", "mystery", "drama", "comedy", "sci-fi", "horror", "action",
            "racing", "sports", "fantasy", "romance", "animation", "documentary",
            "chill", "strategy",
        }
        valid_moods = {"dark", "calm", "nostalgic", "energetic", "surreal"}
        valid_media = {"movie", "series", "music", "game"}
        valid_lang = {"tr", "ko", "ja", "es", "fr", "it", "de", "zh", "hi", "pt", "sv"}

        genres = [g for g in (data.get("genres") or []) if g in valid_genres]
        moods = [m for m in (data.get("moods") or []) if m in valid_moods]
        media_type = data.get("media_type") if data.get("media_type") in valid_media else None
        language = data.get("language") if data.get("language") in valid_lang else None
        era = data.get("era") if isinstance(data.get("era"), str) else None
        similar_to = data.get("similar_to") if isinstance(data.get("similar_to"), str) else None
        seed_titles = [t for t in (data.get("seed_titles") or []) if isinstance(t, str) and t][:5]

        def _as_year(v):
            try:
                y = int(v)
                return y if 1900 <= y <= 2100 else None
            except (TypeError, ValueError):
                return None
        year_min = _as_year(data.get("year_min"))
        year_max = _as_year(data.get("year_max"))
        reply = data.get("reply") if isinstance(data.get("reply"), str) and data.get("reply").strip() else None

        intent = UserIntent(
            raw_text=text,
            media_type=media_type,
            genres=genres,
            moods=moods,
            era=era,
            similar_to=similar_to,
            language=language,
            seed_titles=seed_titles,
            year_min=year_min,
            year_max=year_max,
        )
        return reply, intent
