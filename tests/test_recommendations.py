from app.api.schemas import RecommendationRequest, StatedPreferences
from app.models.product import Product
from app.services.recommendations.engine import ContentBasedRecommender


def test_cold_start_recommendations(db_session):
    products = db_session.query(Product).all()
    recommender = ContentBasedRecommender(products)

    req = RecommendationRequest(
        user_id="new_user_123",
        preferences=None,
        viewed_product_ids=[],
        saved_product_ids=[],
        top_k=6,
    )
    resp = recommender.recommend(req)

    assert resp.is_cold_start is True
    assert len(resp.recommendations) > 0
    # Must showcase multiple distinct categories
    cats = {item.product.category for item in resp.recommendations}
    assert len(cats) >= 4, f"Cold start should provide diverse categories, got {cats}"


def test_recommendation_stated_preferences(db_session):
    products = db_session.query(Product).all()
    recommender = ContentBasedRecommender(products)

    req = RecommendationRequest(
        user_id="user_scandi",
        preferences=StatedPreferences(
            category="desks",
            preferred_styles=["scandinavian"],
            budget_max=16000.0,
        ),
        top_k=4,
    )
    resp = recommender.recommend(req)

    assert resp.is_cold_start is False
    assert len(resp.recommendations) > 0
    top = resp.recommendations[0].product
    assert top.category == "desks"
    assert top.price <= 16000.0


def test_recommendation_saved_history_boosting(db_session):
    products = db_session.query(Product).all()
    recommender = ContentBasedRecommender(products)

    # User saved a velvet modern armchair
    req = RecommendationRequest(
        user_id="user_velvet",
        saved_product_ids=["FUR-CHR-005"],  # Cantilever Velvet Dining Chair
        top_k=4,
    )
    resp = recommender.recommend(req)

    assert resp.is_cold_start is False
    # The saved product itself should be excluded from recommendations
    recommended_ids = [item.product.product_id for item in resp.recommendations]
    assert "FUR-CHR-005" not in recommended_ids
    # Should feature related chairs/velvet/modern items
    has_relevant = any(
        "velvet" in (item.product.material or "")
        or "modern" in (item.product.style or "")
        or item.product.category == "chairs"
        for item in resp.recommendations
    )
    assert has_relevant
