from core.chatbot.intent_parser import IntentParser


def test_parser_detects_series_crime_and_era() -> None:
    intent = IntentParser().parse("90'lar Amerika'sında geçen Twin Peaks tarzı suç dizisi")

    assert intent.media_type == "series"
    assert "crime" in intent.genres
    assert intent.era == "1990s"
