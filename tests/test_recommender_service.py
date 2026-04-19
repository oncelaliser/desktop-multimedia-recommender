from core.recommendation.recommender_service import RecommenderService


def test_recommender_returns_ranked_items() -> None:
    recommendations = RecommenderService().recommend(
        "90'lar Amerika'sında geçen karanlık suç dizisi",
        selected_media_type="Series",
    )

    assert recommendations
    assert recommendations[0].score >= recommendations[-1].score
