import io

from PIL import Image


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True


def test_products_list_and_pagination(client):
    response = client.get("/api/v1/products?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) == 5
    assert data["page"] == 1


def test_products_filter_category(client):
    response = client.get("/api/v1/products?category=desks")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for p in data["items"]:
        assert p["category"] == "desks"


def test_product_detail_and_404(client):
    # Valid product
    response = client.get("/api/v1/products/FUR-DSK-001")
    assert response.status_code == 200
    assert response.json()["product_id"] == "FUR-DSK-001"

    # Non-existent product
    not_found = client.get("/api/v1/products/NON-EXISTENT-999")
    assert not_found.status_code == 404


def test_search_endpoint_hybrid(client):
    payload = {
        "query": "Scandinavian oak desk under 15000",
        "search_mode": "hybrid",
        "top_k": 5,
    }
    response = client.post("/api/v1/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["extracted_filters"]["category"] == "desks"
    assert data["extracted_filters"]["max_price"] == 15000.0


def test_recommendations_endpoint(client):
    payload = {
        "user_id": "test_user",
        "preferences": {
            "category": "chairs",
            "preferred_styles": ["modern"],
            "budget_max": 20000.0,
        },
        "top_k": 4,
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0


def test_assistant_endpoint(client):
    payload = {"question": "Which desk is the narrowest and costs less than ₹15,000?"}
    response = client.post("/api/v1/assistant/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert "answer" in data
    assert len(data["structured_evidence"]) > 0


def test_image_search_endpoint(client):
    img = Image.new("RGB", (80, 80), color="tan")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/v1/search/image", files={"file": ("reference.png", buf, "image/png")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "encoder_used" in data


def test_analytics_search_evaluation_endpoint(client):
    response = client.get("/api/v1/analytics/search-evaluation")
    assert response.status_code == 200
    data = response.json()
    assert "comparison" in data
    assert "keyword" in data["comparison"]
    assert "hybrid" in data["comparison"]
