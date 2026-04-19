# Desktop Multimedia Recommender

Early iteration of a Python desktop application for multimedia recommendations.

The project is intentionally modular:

- `ui/` contains only PyQt screens and widgets.
- `core/chatbot/` contains provider-based chatbot logic.
- `core/recommendation/` contains ranking, scoring, and explanation logic.
- `integrations/` is reserved for external APIs such as TMDB, OMDb, Spotify, and LM Studio/OpenAI-compatible providers.
- `data/` is reserved for SQLite persistence and domain models.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Current Scope

This first iteration includes:

- PyQt6 GUI
- Chat screen
- AI mode selector
- Offline template chatbot provider
- LM Studio provider scaffold
- OpenAI-compatible provider scaffold
- Local mock recommendation engine
- Explainable scoring placeholders

MiniLM, real API clients, and SQLite persistence are designed as next-step integrations.
