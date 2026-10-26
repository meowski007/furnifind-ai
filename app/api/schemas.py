from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# --- Product Schemas ---


class ProductBase(BaseModel):
    product_id: str
    title: str
    description: str
    category: str
    price: float
    currency: str = "INR"
    material: str | None = None
    colour: str | None = None
    style: str | None = None
    width: float | None = None
    height: float | None = None
    depth: float | None = None
    image_path: str | None = None
    image_url: str | None = None
    availability: bool = True
    source: str = "furnifind_catalogue"


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime | str | None = None


class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductResponse]


# --- Search Schemas ---


class ExtractedFilters(BaseModel):
    category: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    colour: str | None = None
    material: str | None = None
    style: str | None = None
    max_width_cm: float | None = None
    min_width_cm: float | None = None
    availability: bool | None = None


class SearchFilters(BaseModel):
    category: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    colour: str | None = None
    material: str | None = None
    style: str | None = None
    min_width: float | None = None
    max_width: float | None = None
    availability: bool | None = None


class SearchRequest(BaseModel):
    query: str = Field(
        ..., min_length=1, max_length=500, description="Natural language search query"
    )
    search_mode: str = Field(
        "hybrid", description="Retriever mode: 'keyword', 'semantic', or 'hybrid'"
    )
    filters: SearchFilters | None = None
    top_k: int = Field(10, ge=1, le=50)
    alpha: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Weight for semantic score in hybrid search (0=keyword only, 1=semantic only)",
    )


class SearchResultItem(BaseModel):
    product: ProductResponse
    score: float
    keyword_score: float | None = None
    semantic_score: float | None = None
    match_explanation: str


class SearchResponse(BaseModel):
    query: str
    search_mode: str
    extracted_filters: ExtractedFilters
    applied_filters: dict[str, Any]
    total_matches: int
    results: list[SearchResultItem]
    latency_ms: float
    suggestions: list[str] = []


# --- Image Search Schemas ---


class ImageSearchResultItem(BaseModel):
    product: ProductResponse
    similarity_score: float
    visual_match_explanation: str


class ImageSearchResponse(BaseModel):
    total_matches: int
    results: list[ImageSearchResultItem]
    latency_ms: float
    encoder_used: str


# --- Recommendation Schemas ---


class StatedPreferences(BaseModel):
    category: str | None = None
    budget_max: float | None = None
    preferred_styles: list[str] = []
    preferred_materials: list[str] = []
    preferred_colours: list[str] = []


class RecommendationRequest(BaseModel):
    user_id: str | None = "guest"
    preferences: StatedPreferences | None = None
    viewed_product_ids: list[str] = []
    saved_product_ids: list[str] = []
    top_k: int = Field(6, ge=1, le=20)
    include_diversity: bool = True


class RecommendationItem(BaseModel):
    product: ProductResponse
    recommendation_score: float
    recommendation_reasons: list[str]
    explanation: str


class RecommendationResponse(BaseModel):
    user_id: str
    is_cold_start: bool
    total_recommendations: int
    recommendations: list[RecommendationItem]
    strategy_summary: str


# --- Assistant Q&A Schemas ---


class AssistantAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)
    focus_product_ids: list[str] | None = None


class AssistantFactItem(BaseModel):
    product_id: str
    title: str
    attribute: str
    value: Any


class AssistantAskResponse(BaseModel):
    question: str
    answer: str
    grounded: bool
    structured_evidence: list[AssistantFactItem]
    referenced_products: list[ProductResponse]
    missing_data_notes: str | None = None
    used_llm: bool


# --- Evaluation Schemas ---


class MetricSet(BaseModel):
    precision_at_5: float
    recall_at_5: float
    ndcg_at_5: float
    mrr: float
    empty_result_rate: float


class QueryEvaluationResult(BaseModel):
    query_id: str
    query: str
    query_type: str
    ground_truth_count: int
    retrieved_count: int
    precision_at_5: float
    recall_at_5: float
    ndcg_at_5: float


class MethodComparison(BaseModel):
    keyword: MetricSet
    semantic: MetricSet
    hybrid: MetricSet


class EvaluationResponse(BaseModel):
    total_queries: int
    comparison: MethodComparison
    query_details: list[QueryEvaluationResult]
    analysis_notes: str
    timestamp: str
