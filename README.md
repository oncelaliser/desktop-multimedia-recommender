# Desktop Multimedia Recommender

Python/PyQt6 desktop application that accepts natural language prompts and returns ranked, explainable media recommendations across movies, series, music, and games.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then edit .env with your API keys
python main.py
```

## API Keys

Copy `.env.example` to `.env` and fill in the keys you have. All are optional — the app falls back to a built-in sample catalog when no external APIs are configured.

| Key | Source | Enables |
|-----|--------|---------|
| `TMDB_API_KEY` | [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) (free) | Live movie & series search |
| `OMDB_API_KEY` | [omdbapi.com/apikey.aspx](https://www.omdbapi.com/apikey.aspx) (free tier) | IMDb rating enrichment |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) (free) | Music recommendations |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | Cloud LLM chatbot |

LM Studio mode requires [LM Studio](https://lmstudio.ai) to be running locally with a model loaded.

## Architecture

```
ui/                 PyQt6 windows, chatbot panel, recommendation cards
core/chatbot/       Provider-based chatbot (Offline / OpenAI / LM Studio)
core/recommendation/  Intent parsing, scoring engine, explanation builder
integrations/       API clients: TMDB, OMDb, Spotify
data/               SQLite repositories, domain models
app/                Config, constants, logging
```

**Recommendation flow:** natural language prompt → intent parser extracts media type / genre / mood / era → TMDB or Spotify fetch live candidates → weighted scoring (semantic similarity 35%, genre 20%, type 15%, mood 10%, era 10%, rating 5%, popularity 5%) → ranked explainable cards.

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## AI Modes

| Mode | Description |
|------|-------------|
| Offline Basic | Template-based, works without internet or API keys |
| OpenAI-Compatible API | Any OpenAI-compatible endpoint (OpenAI, local vLLM, etc.) |
| LM Studio Local | Local LLM via LM Studio's built-in server |
