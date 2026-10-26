from collections import Counter

from app.api.schemas import (
    ProductResponse,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
    StatedPreferences,
)
from app.models.product import Product


class ContentBasedRecommender:
    """Explainable content-based recommendation engine with cold-start and diversity controls."""

    def __init__(self, products: list[Product]):
        self.products = products
        self.product_by_id: dict[str, Product] = {p.product_id: p for p in products}

    def recommend(self, req: RecommendationRequest) -> RecommendationResponse:
        prefs = req.preferences or StatedPreferences()
        viewed_ids = set(req.viewed_product_ids)
        saved_ids = set(req.saved_product_ids)

        is_cold_start = (
            len(viewed_ids) == 0
            and len(saved_ids) == 0
            and not prefs.category
            and not prefs.preferred_styles
            and not prefs.preferred_materials
            and prefs.budget_max is None
        )

        # 1. Cold start scenario (no history, no explicit preferences)
        if is_cold_start:
            return self._cold_start_recommendations(req)

        # 2. Extract profile vectors from history and explicit preferences
        style_affinities: Counter = Counter()
        material_affinities: Counter = Counter()
        category_affinities: Counter = Counter()
        colour_affinities: Counter = Counter()
        interacted_prices: list[float] = []

        # Add explicit preferences with high weight
        for s in prefs.preferred_styles:
            style_affinities[s.lower()] += 3.0
        for m in prefs.preferred_materials:
            material_affinities[m.lower()] += 3.0
        for c in prefs.preferred_colours:
            colour_affinities[c.lower()] += 2.0
        if prefs.category:
            category_affinities[prefs.category.lower()] += 4.0

        # Add saved items (weight 2.0)
        for pid in saved_ids:
            if pid in self.product_by_id:
                p = self.product_by_id[pid]
                interacted_prices.append(p.price)
                if p.style:
                    style_affinities[p.style.lower()] += 2.0
                if p.material:
                    material_affinities[p.material.lower()] += 2.0
                if p.colour:
                    colour_affinities[p.colour.lower()] += 1.5
                category_affinities[p.category.lower()] += 2.0

        # Add viewed items (weight 1.0)
        for pid in viewed_ids:
            if pid in self.product_by_id:
                p = self.product_by_id[pid]
                interacted_prices.append(p.price)
                if p.style:
                    style_affinities[p.style.lower()] += 1.0
                if p.material:
                    material_affinities[p.material.lower()] += 1.0
                if p.colour:
                    colour_affinities[p.colour.lower()] += 0.8
                category_affinities[p.category.lower()] += 1.0

        # Target budget reference
        target_budget = prefs.budget_max
        if target_budget is None and interacted_prices:
            # Use 80th percentile of interacted items
            target_budget = max(interacted_prices) * 1.2

        # 3. Score all available products
        candidates: list[RecommendationItem] = []
        excluded_ids = saved_ids | (viewed_ids if len(self.products) > 15 else set())

        for p in self.products:
            if p.product_id in excluded_ids:
                continue

            reasons: list[str] = []
            score: float = 0.0

            # Category score (max 0.25)
            cat_lower = p.category.lower()
            if cat_lower in category_affinities:
                cat_weight = min(0.25, 0.10 + 0.05 * category_affinities[cat_lower])
                score += cat_weight
                reasons.append(f"Matches category interest in {p.category}")

            # Style score (max 0.25)
            if p.style and p.style.lower() in style_affinities:
                st_weight = min(0.25, 0.12 + 0.04 * style_affinities[p.style.lower()])
                score += st_weight
                reasons.append(
                    f"Consistent with your affinity for {p.style} aesthetics"
                )

            # Material score (max 0.20)
            if p.material and p.material.lower() in material_affinities:
                mat_weight = min(
                    0.20, 0.10 + 0.03 * material_affinities[p.material.lower()]
                )
                score += mat_weight
                reasons.append(f"Features {p.material} material")

            # Colour score (max 0.15)
            if p.colour and p.colour.lower() in colour_affinities:
                col_weight = min(
                    0.15, 0.08 + 0.02 * colour_affinities[p.colour.lower()]
                )
                score += col_weight
                reasons.append(f"Matches your preference for {p.colour}")

            # Price suitability score (max 0.15)
            if target_budget is not None:
                if p.price <= target_budget:
                    score += 0.15
                    reasons.append(
                        f"Well within your target budget (₹{p.price:,.0f} ≤ ₹{target_budget:,.0f})"
                    )
                else:
                    # Soft penalty for exceeding budget
                    over_ratio = (p.price - target_budget) / target_budget
                    penalty = max(-0.25, -0.15 * over_ratio)
                    score += penalty
            else:
                score += 0.08

            if score > 0.10:
                explanation = (
                    "; ".join(reasons)
                    if reasons
                    else "Selected based on catalogue popularity"
                )
                candidates.append(
                    RecommendationItem(
                        product=ProductResponse.model_validate(p),
                        recommendation_score=round(score, 4),
                        recommendation_reasons=reasons,
                        explanation=explanation,
                    )
                )

        # 4. Diversity re-ranking: prevent single category dominating all slots
        candidates.sort(key=lambda x: x.recommendation_score, reverse=True)

        if req.include_diversity:
            selected: list[RecommendationItem] = []
            category_counts: dict[str, int] = {}
            max_per_category = max(1, req.top_k // 2)

            for cand in candidates:
                cat = cand.product.category
                if category_counts.get(cat, 0) < max_per_category:
                    selected.append(cand)
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                if len(selected) >= req.top_k:
                    break

            # If not enough picked due to category caps, fill from remaining
            if len(selected) < req.top_k:
                for cand in candidates:
                    if cand not in selected:
                        selected.append(cand)
                    if len(selected) >= req.top_k:
                        break
            final_recommendations = selected
        else:
            final_recommendations = candidates[: req.top_k]

        return RecommendationResponse(
            user_id=req.user_id or "guest",
            is_cold_start=False,
            total_recommendations=len(final_recommendations),
            recommendations=final_recommendations,
            strategy_summary=f"Personalized content-based filtering derived from {len(saved_ids)} saved items, {len(viewed_ids)} viewed items, and stated preferences.",
        )

    def _cold_start_recommendations(
        self, req: RecommendationRequest
    ) -> RecommendationResponse:
        """Cold-start strategy: curate high-rated, highly diverse anchor products across distinct categories."""
        # Pick 1 representative item from each distinct category
        seen_cats = set()
        picked = []

        # Categories order for diverse home showcase
        showcase_order = [
            "desks",
            "chairs",
            "sofas",
            "tables",
            "beds",
            "bookcases",
            "storage",
            "lighting",
        ]

        for target_cat in showcase_order:
            for p in self.products:
                if (
                    p.category == target_cat
                    and p.product_id not in seen_cats
                    and p.availability
                ):
                    seen_cats.add(p.product_id)
                    picked.append(
                        RecommendationItem(
                            product=ProductResponse.model_validate(p),
                            recommendation_score=0.90,
                            recommendation_reasons=[
                                "Popular catalogue showcase",
                                f"Category anchor: {p.category}",
                            ],
                            explanation=f"Top-rated {p.category} selection for new customers.",
                        )
                    )
                    break
            if len(picked) >= req.top_k:
                break

        return RecommendationResponse(
            user_id=req.user_id or "guest",
            is_cold_start=True,
            total_recommendations=len(picked),
            recommendations=picked,
            strategy_summary="Cold-start onboarding: Curated catalog discovery showcasing diverse categories and popular designs.",
        )
