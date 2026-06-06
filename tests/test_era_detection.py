from core.chatbot.intent_parser import IntentParser
from core.recommendation.scoring_engine import ScoringEngine
from data.models.media_item import MediaItem


def _item(year: int) -> MediaItem:
    return MediaItem(id="x", title="X", media_type="movie", description="", release_year=year)


def test_era_detection_various_formats() -> None:
    p = IntentParser()
    assert p.parse("70s thriller").era == "1970s"
    assert p.parse("1970s film").era == "1970s"
    assert p.parse("70'lar gerilim").era == "1970s"
    assert p.parse("2010s sci-fi").era == "2010s"
    assert p.parse("1985 western").era == "1980s"
    assert p.parse("klasik sinema").era is None


def test_era_score_exact_match() -> None:
    from core.chatbot.intent_parser import UserIntent
    engine = ScoringEngine()
    intent = UserIntent(raw_text="", era="1990s")
    assert engine._era_score("1990s", 1995) == 1.0
    assert engine._era_score("1990s", 1990) == 1.0
    assert engine._era_score("1990s", 1999) == 1.0


def test_era_score_adjacent_decade() -> None:
    assert ScoringEngine()._era_score("1990s", 2003) == 0.4


def test_era_score_no_match() -> None:
    assert ScoringEngine()._era_score("1990s", 1950) == 0.0


def test_era_score_none_era_returns_neutral() -> None:
    assert ScoringEngine()._era_score(None, 1995) == 0.5
