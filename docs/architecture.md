# Architecture

The application is split into replaceable layers.

## UI

`ui/` contains PyQt6 widgets. It should not call external APIs directly and should not contain recommendation logic.

## Chatbot

`core/chatbot/` uses a provider interface:

- `OfflineTemplateProvider`
- `OpenAICompatibleProvider`
- `LMStudioProvider`

New providers can be added without changing the UI.

## Recommendation

`core/recommendation/` owns the recommendation pipeline:

1. Parse user intent.
2. Gather candidate media.
3. Score candidates.
4. Rank candidates.
5. Build explanations.

The current `SimilarityEngine` is a lightweight placeholder. A MiniLM embedding engine can later replace it behind the same scoring boundary.

## Data

`data/db/schema.sql` defines the intended SQLite structure for media items, API cache, and embeddings.

## Integration Rule

External LLMs must not invent the final recommendation list. They may help with conversation and intent extraction, but final results should come from API/SQLite candidates ranked by `RecommenderService`.
