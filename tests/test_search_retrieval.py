from app.api.schemas import SearchRequest
from app.models.product import Product
from app.services.search.hybrid_search import HybridSearchEngine
from app.services.search.keyword_search import BM25SearchEngine
from app.services.search.semantic_search import SemanticSearchEngine


def test_keyword_search_exact_match(db_session):
    products = db_session.query(Product).all()
    kw_engine = BM25SearchEngine()
    kw_engine.fit(products)

    results = kw_engine.search("Nordic Light Oak Study Desk", top_k=5)
    assert len(results) > 0
    top_product = results[0][0]
    assert top_product.product_id == "FUR-DSK-001"
    assert "oak" in results[0][2]


def test_hybrid_search_hard_constraint_budget(db_session):
    products = db_session.query(Product).all()
    kw_engine = BM25SearchEngine()
    kw_engine.fit(products)
    sem_engine = SemanticSearchEngine()
    sem_engine.fit(products)
    hybrid_engine = HybridSearchEngine(kw_engine, sem_engine)

    # Budget strictly capped at 12000
    req = SearchRequest(
        query="industrial desk under 12000", search_mode="hybrid", top_k=5
    )
    resp = hybrid_engine.search(req)

    assert resp.total_matches > 0
    for item in resp.results:
        assert item.product.price <= 12000.0, (
            f"Product {item.product.product_id} price {item.product.price} exceeded 12000"
        )


def test_hybrid_search_hard_constraint_width(db_session):
    products = db_session.query(Product).all()
    kw_engine = BM25SearchEngine()
    kw_engine.fit(products)
    sem_engine = SemanticSearchEngine()
    sem_engine.fit(products)
    hybrid_engine = HybridSearchEngine(kw_engine, sem_engine)

    # Request width below 110 cm
    req = SearchRequest(
        query="study desk width below 110 cm", search_mode="hybrid", top_k=5
    )
    resp = hybrid_engine.search(req)

    assert resp.total_matches > 0
    for item in resp.results:
        assert item.product.width is not None
        assert item.product.width <= 110.0, (
            f"Product {item.product.product_id} width {item.product.width} exceeded 110 cm"
        )


def test_out_of_catalogue_negative_query(db_session):
    products = db_session.query(Product).all()
    kw_engine = BM25SearchEngine()
    kw_engine.fit(products)
    sem_engine = SemanticSearchEngine()
    sem_engine.fit(products)
    hybrid_engine = HybridSearchEngine(kw_engine, sem_engine)

    req = SearchRequest(
        query="neon pink inflatable pool lounger with solar heater",
        search_mode="keyword",
        top_k=5,
    )
    resp = hybrid_engine.search(req)
    assert len(resp.results) == 0
    assert len(resp.suggestions) > 0


def test_explanation_grounding(db_session):
    products = db_session.query(Product).all()
    kw_engine = BM25SearchEngine()
    kw_engine.fit(products)
    sem_engine = SemanticSearchEngine()
    sem_engine.fit(products)
    hybrid_engine = HybridSearchEngine(kw_engine, sem_engine)

    req = SearchRequest(
        query="Scandinavian light oak desk under 15000", search_mode="hybrid", top_k=1
    )
    resp = hybrid_engine.search(req)

    assert len(resp.results) > 0
    exp = resp.results[0].match_explanation
    assert "budget" in exp.lower() or "price" in exp.lower()
    assert "oak" in exp.lower()
