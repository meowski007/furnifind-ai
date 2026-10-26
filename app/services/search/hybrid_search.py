import time

from app.api.schemas import (
    ExtractedFilters,
    ProductResponse,
    SearchFilters,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.models.product import Product
from app.services.search.keyword_search import BM25SearchEngine
from app.services.search.query_parser import QueryParser
from app.services.search.semantic_search import SemanticSearchEngine


class HybridSearchEngine:
    def __init__(
        self, keyword_engine: BM25SearchEngine, semantic_engine: SemanticSearchEngine
    ):
        self.keyword_engine = keyword_engine
        self.semantic_engine = semantic_engine

    @staticmethod
    def apply_hard_filters(
        product: Product,
        extracted: ExtractedFilters,
        manual_filters: SearchFilters | None,
    ) -> bool:
        # Check explicit manual filters first, fallback to extracted filters
        max_p = None
        if manual_filters and manual_filters.max_price is not None:
            max_p = manual_filters.max_price
        elif extracted.max_price is not None:
            max_p = extracted.max_price

        if max_p is not None and product.price > max_p:
            return False

        min_p = None
        if manual_filters and manual_filters.min_price is not None:
            min_p = manual_filters.min_price
        elif extracted.min_price is not None:
            min_p = extracted.min_price

        if min_p is not None and product.price < min_p:
            return False

        # Category constraint
        req_cat = None
        if manual_filters and manual_filters.category:
            req_cat = manual_filters.category.lower()
        elif extracted.category:
            req_cat = extracted.category.lower()

        if req_cat and product.category.lower() != req_cat:
            return False

        # Max width constraint (if product has width specified and filter exists)
        max_w = None
        if manual_filters and manual_filters.max_width is not None:
            max_w = manual_filters.max_width
        elif extracted.max_width_cm is not None:
            max_w = extracted.max_width_cm

        if max_w is not None:
            # If product has no width recorded, or width exceeds max_w, reject
            if product.width is None or product.width > max_w:
                return False

        # Style constraint
        req_style = None
        if manual_filters and manual_filters.style:
            req_style = manual_filters.style.lower()
        elif extracted.style:
            req_style = extracted.style.lower()

        if req_style and (not product.style or req_style not in product.style.lower()):
            return False

        # Material constraint
        req_mat = None
        if manual_filters and manual_filters.material:
            req_mat = manual_filters.material.lower()
        elif extracted.material:
            req_mat = extracted.material.lower()

        if req_mat and (
            not product.material or req_mat not in product.material.lower()
        ):
            return False

        # Colour constraint
        req_col = None
        if manual_filters and manual_filters.colour:
            req_col = manual_filters.colour.lower()
        elif extracted.colour:
            req_col = extracted.colour.lower()

        if req_col and (not product.colour or req_col not in product.colour.lower()):
            return False

        # Availability constraint
        if (
            manual_filters
            and manual_filters.availability is True
            and not product.availability
        ):
            return False

        return True

    @staticmethod
    def generate_explanation(
        product: Product,
        query: str,
        extracted: ExtractedFilters,
        matched_terms: list[str],
        kw_score: float,
        sem_score: float,
    ) -> str:
        reasons = []

        if extracted.category and product.category == extracted.category:
            reasons.append(f"Matches category '{product.category}'")

        if extracted.max_price and product.price <= extracted.max_price:
            reasons.append(
                f"Within budget (₹{product.price:,.0f} <= ₹{extracted.max_price:,.0f})"
            )

        if (
            extracted.max_width_cm
            and product.width is not None
            and product.width <= extracted.max_width_cm
        ):
            reasons.append(
                f"Width of {product.width} cm fits within your {extracted.max_width_cm} cm limit"
            )

        if (
            extracted.material
            and product.material
            and extracted.material in product.material.lower()
        ):
            reasons.append(f"Crafted from {product.material}")

        if (
            extracted.style
            and product.style
            and extracted.style in product.style.lower()
        ):
            reasons.append(f"{product.style.capitalize()} aesthetic")

        if (
            extracted.colour
            and product.colour
            and extracted.colour in product.colour.lower()
        ):
            reasons.append(f"{product.colour.capitalize()} finish")

        if matched_terms:
            unique_terms = sorted(list(set(matched_terms)))[:3]
            reasons.append(f"Contains matching terms: {', '.join(unique_terms)}")

        if not reasons:
            if sem_score > 0.5:
                reasons.append(
                    f"Strong conceptual match ({sem_score:.0%} semantic similarity) to '{query}'"
                )
            elif kw_score > 0.3:
                reasons.append("Relevant product specifications match your search")
            else:
                reasons.append("General catalogue match")

        return "; ".join(reasons) + "."

    def search(self, request: SearchRequest) -> SearchResponse:
        start_time = time.perf_counter()
        raw_query = request.query
        extracted, residual = QueryParser.parse_query(raw_query)

        # 1. Retrieve candidates
        kw_results = self.keyword_engine.search(residual, top_k=50)
        sem_results = self.semantic_engine.search(residual, top_k=50)

        kw_map: dict[str, tuple[Product, float, list[str]]] = {
            p.product_id: (p, score, terms) for p, score, terms in kw_results
        }
        sem_map: dict[str, tuple[Product, float]] = {
            p.product_id: (p, score) for p, score in sem_results
        }

        # Candidate union of products
        all_candidate_ids = set(kw_map.keys()) | set(sem_map.keys())

        scored_candidates: list[SearchResultItem] = []

        alpha = (
            request.alpha
            if request.search_mode == "hybrid"
            else (1.0 if request.search_mode == "semantic" else 0.0)
        )

        for pid in all_candidate_ids:
            p = kw_map[pid][0] if pid in kw_map else sem_map[pid][0]

            # Enforce hard constraints (filter out violators)
            if not self.apply_hard_filters(p, extracted, request.filters):
                continue

            kw_score = kw_map[pid][1] if pid in kw_map else 0.0
            kw_terms = kw_map[pid][2] if pid in kw_map else []
            sem_score = sem_map[pid][1] if pid in sem_map else 0.0

            if request.search_mode == "keyword":
                final_score = kw_score
            elif request.search_mode == "semantic":
                final_score = sem_score
            else:
                # Hybrid weighted blend
                final_score = (1.0 - alpha) * kw_score + alpha * sem_score

            if final_score > 0.02:
                explanation = self.generate_explanation(
                    product=p,
                    query=raw_query,
                    extracted=extracted,
                    matched_terms=kw_terms,
                    kw_score=kw_score,
                    sem_score=sem_score,
                )
                scored_candidates.append(
                    SearchResultItem(
                        product=ProductResponse.model_validate(p),
                        score=round(final_score, 4),
                        keyword_score=round(kw_score, 4),
                        semantic_score=round(sem_score, 4),
                        match_explanation=explanation,
                    )
                )

        # Sort descending by final score
        scored_candidates.sort(key=lambda x: x.score, reverse=True)
        top_results = scored_candidates[: request.top_k]

        latency = (time.perf_counter() - start_time) * 1000.0

        applied_filters_dict = {}
        if request.filters:
            applied_filters_dict = {
                k: v for k, v in request.filters.model_dump().items() if v is not None
            }

        suggestions = []
        if not top_results:
            suggestions = [
                "Try widening your budget range.",
                "Try removing dimension or width constraints.",
                "Search with broader categories like 'desk', 'chair', or 'table'.",
                "Explore available materials such as 'oak', 'walnut', or 'velvet'.",
            ]

        return SearchResponse(
            query=raw_query,
            search_mode=request.search_mode,
            extracted_filters=extracted,
            applied_filters=applied_filters_dict,
            total_matches=len(scored_candidates),
            results=top_results,
            latency_ms=round(latency, 2),
            suggestions=suggestions,
        )
