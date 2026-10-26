import re

from app.api.schemas import (
    AssistantAskRequest,
    AssistantAskResponse,
    AssistantFactItem,
    ProductResponse,
)
from app.models.product import Product
from app.services.assistant.guardrails import AssistantGuardrails
from app.services.search.hybrid_search import HybridSearchEngine
from app.services.search.query_parser import QueryParser


class AssistantRAGEngine:
    """Grounded Product Question-Answering engine using exact SQL/Python retrieval & optional LLM synthesis."""

    def __init__(self, products: list[Product], hybrid_engine: HybridSearchEngine):
        self.products = products
        self.product_by_id = {p.product_id: p for p in products}
        self.hybrid_engine = hybrid_engine

    def answer_question(self, req: AssistantAskRequest) -> AssistantAskResponse:
        raw_question = req.question.strip()

        # 1. Guardrails check
        sanitized_q, is_suspicious = AssistantGuardrails.sanitize_and_check_injection(
            raw_question
        )
        if is_suspicious:
            return AssistantAskResponse(
                question=raw_question,
                answer="I cannot fulfill this request because it contains prompt manipulation or disallowed security instructions. I can only assist with factual furniture inquiries from our catalogue.",
                grounded=True,
                structured_evidence=[],
                referenced_products=[],
                missing_data_notes=None,
                used_llm=False,
            )

        # 2. Check for out-of-scope non-furniture questions
        q_lower = sanitized_q.lower()
        furniture_keywords = [
            "desk",
            "chair",
            "sofa",
            "couch",
            "table",
            "bed",
            "bookcase",
            "shelf",
            "storage",
            "lamp",
            "lighting",
            "credenza",
            "futon",
            "furniture",
            "price",
            "cost",
            "width",
            "height",
            "depth",
            "dimension",
            "material",
            "wood",
            "oak",
            "walnut",
            "leather",
            "fabric",
            "colour",
            "cheapest",
            "narrowest",
            "widest",
            "highest",
            "available",
            "stock",
            "fur-",
        ]
        if not any(k in q_lower for k in furniture_keywords):
            return AssistantAskResponse(
                question=raw_question,
                answer="I am FurniFind AI's shopping assistant specialized exclusively in furniture discovery, specifications, comparisons, and dimensions from our verified catalogue. Please ask a question related to our furniture products.",
                grounded=True,
                structured_evidence=[],
                referenced_products=[],
                missing_data_notes=None,
                used_llm=False,
            )

        # 3. Question Classification
        # Type A: Superlative / Numerical comparison (e.g. "narrowest desk under 15000", "cheapest sofa")
        superlative_match = self._handle_superlative_query(q_lower, raw_question)
        if superlative_match:
            return superlative_match

        # Type B: Specific Product by ID or Title inquiry
        direct_product_match = self._handle_specific_product_query(
            q_lower, raw_question
        )
        if direct_product_match:
            return direct_product_match

        # Type C: General RAG Retrieval over Catalogue
        return self._handle_general_retrieval_query(sanitized_q)

    def _handle_superlative_query(
        self, q_lower: str, raw_question: str
    ) -> AssistantAskResponse | None:
        extracted_filters, _ = QueryParser.parse_query(q_lower)
        target_cat = extracted_filters.category

        # Attribute to compare
        is_narrowest = (
            "narrowest" in q_lower
            or "smallest width" in q_lower
            or "least wide" in q_lower
        )
        is_widest = "widest" in q_lower or "largest width" in q_lower
        is_cheapest = (
            "cheapest" in q_lower
            or "lowest price" in q_lower
            or "least expensive" in q_lower
        )
        is_most_expensive = "most expensive" in q_lower or "highest price" in q_lower

        if not (is_narrowest or is_widest or is_cheapest or is_most_expensive):
            return None

        # Filter candidates by category & price constraints
        candidates = self.products
        if target_cat:
            candidates = [p for p in candidates if p.category == target_cat]

        if extracted_filters.max_price is not None:
            candidates = [
                p for p in candidates if p.price <= extracted_filters.max_price
            ]

        if extracted_filters.min_price is not None:
            candidates = [
                p for p in candidates if p.price >= extracted_filters.min_price
            ]

        if not candidates:
            cat_label = f"in category '{target_cat}'" if target_cat else ""
            budget_label = (
                f"under ₹{extracted_filters.max_price:,.0f}"
                if extracted_filters.max_price
                else ""
            )
            return AssistantAskResponse(
                question=raw_question,
                answer=f"No products found matching your criteria {cat_label} {budget_label} in the current catalogue.",
                grounded=True,
                structured_evidence=[],
                referenced_products=[],
                missing_data_notes="No matching catalogue items met all hard constraints.",
                used_llm=False,
            )

        evidence = []
        referenced = []

        if is_narrowest:
            # Filter products that actually have width specified
            with_dim = [p for p in candidates if p.width is not None]
            if not with_dim:
                return AssistantAskResponse(
                    question=raw_question,
                    answer="None of the matched items have verified width dimensions recorded in the catalogue.",
                    grounded=True,
                    structured_evidence=[],
                    referenced_products=[],
                    missing_data_notes="Width attribute is missing for candidates.",
                    used_llm=False,
                )
            sorted_candidates = sorted(with_dim, key=lambda x: x.width)
            best = sorted_candidates[0]
            answer = (
                f"The narrowest {best.category.removesuffix('s')} "
                f"{f'under ₹{extracted_filters.max_price:,.0f} ' if extracted_filters.max_price else ''}is "
                f"**{best.title}** ({best.product_id}) with a verified width of **{best.width} cm** "
                f"and priced at **₹{best.price:,.0f}**."
            )
            evidence.append(
                AssistantFactItem(
                    product_id=best.product_id,
                    title=best.title,
                    attribute="width",
                    value=f"{best.width} cm",
                )
            )
            evidence.append(
                AssistantFactItem(
                    product_id=best.product_id,
                    title=best.title,
                    attribute="price",
                    value=f"₹{best.price:,.0f}",
                )
            )
            referenced.append(ProductResponse.model_validate(best))

        elif is_widest:
            with_dim = [p for p in candidates if p.width is not None]
            sorted_candidates = sorted(with_dim, key=lambda x: x.width, reverse=True)
            best = sorted_candidates[0]
            answer = (
                f"The widest {best.category.removesuffix('s')} is "
                f"**{best.title}** ({best.product_id}) with a width of **{best.width} cm** "
                f"and priced at **₹{best.price:,.0f}**."
            )
            evidence.append(
                AssistantFactItem(
                    product_id=best.product_id,
                    title=best.title,
                    attribute="width",
                    value=f"{best.width} cm",
                )
            )
            evidence.append(
                AssistantFactItem(
                    product_id=best.product_id,
                    title=best.title,
                    attribute="price",
                    value=f"₹{best.price:,.0f}",
                )
            )
            referenced.append(ProductResponse.model_validate(best))

        elif is_cheapest:
            sorted_candidates = sorted(candidates, key=lambda x: x.price)
            best = sorted_candidates[0]
            answer = (
                f"The most affordable {best.category.removesuffix('s')} is "
                f"**{best.title}** ({best.product_id}) priced at **₹{best.price:,.0f}**."
            )
            evidence.append(
                AssistantFactItem(
                    product_id=best.product_id,
                    title=best.title,
                    attribute="price",
                    value=f"₹{best.price:,.0f}",
                )
            )
            if best.material:
                evidence.append(
                    AssistantFactItem(
                        product_id=best.product_id,
                        title=best.title,
                        attribute="material",
                        value=best.material,
                    )
                )
            referenced.append(ProductResponse.model_validate(best))

        else:  # is_most_expensive
            sorted_candidates = sorted(candidates, key=lambda x: x.price, reverse=True)
            best = sorted_candidates[0]
            answer = (
                f"The highest priced option in this selection is "
                f"**{best.title}** ({best.product_id}) priced at **₹{best.price:,.0f}**."
            )
            evidence.append(
                AssistantFactItem(
                    product_id=best.product_id,
                    title=best.title,
                    attribute="price",
                    value=f"₹{best.price:,.0f}",
                )
            )
            referenced.append(ProductResponse.model_validate(best))

        return AssistantAskResponse(
            question=raw_question,
            answer=answer,
            grounded=True,
            structured_evidence=evidence,
            referenced_products=referenced,
            missing_data_notes=None,
            used_llm=False,
        )

    def _handle_specific_product_query(
        self, q_lower: str, raw_question: str
    ) -> AssistantAskResponse | None:
        # Check for product ID mentions like FUR-DSK-001
        pid_match = re.search(r"(fur-[a-z]{3}-[0-9]{3})", q_lower)
        target_product = None
        if pid_match:
            pid = pid_match.group(1).upper()
            target_product = self.product_by_id.get(pid)

        if not target_product:
            # Check if an exact product title is in question
            for p in self.products:
                if p.title.lower() in q_lower:
                    target_product = p
                    break

        if not target_product:
            return None

        evidence = []
        missing_notes = []

        # Attribute extraction
        p = target_product
        evidence.append(
            AssistantFactItem(
                product_id=p.product_id,
                title=p.title,
                attribute="price",
                value=f"₹{p.price:,.0f}",
            )
        )

        if p.material:
            evidence.append(
                AssistantFactItem(
                    product_id=p.product_id,
                    title=p.title,
                    attribute="material",
                    value=p.material,
                )
            )
        else:
            missing_notes.append("Material is not specified in catalogue records")

        if p.width is not None and p.height is not None and p.depth is not None:
            dims_str = f"{p.width}W x {p.height}H x {p.depth}D cm"
            evidence.append(
                AssistantFactItem(
                    product_id=p.product_id,
                    title=p.title,
                    attribute="dimensions",
                    value=dims_str,
                )
            )
        elif p.width is not None:
            evidence.append(
                AssistantFactItem(
                    product_id=p.product_id,
                    title=p.title,
                    attribute="width",
                    value=f"{p.width} cm",
                )
            )
        else:
            missing_notes.append("Dimensions are not specified for this item")

        evidence.append(
            AssistantFactItem(
                product_id=p.product_id,
                title=p.title,
                attribute="availability",
                value="In stock" if p.availability else "Out of stock",
            )
        )

        # Build response grounded in verified facts
        ans_parts = [
            f"**{p.title}** ({p.product_id}):",
            f"- **Price**: ₹{p.price:,.0f} {p.currency}",
            f"- **Category**: {p.category}",
            f"- **Style**: {p.style or 'Not recorded'}",
            f"- **Material**: {p.material or 'Not recorded'}",
            f"- **Dimensions**: {f'{p.width} x {p.height} x {p.depth} cm' if p.width else 'Not recorded'}",
            f"- **Availability**: {'In Stock' if p.availability else 'Currently Out of Stock'}",
            f"\n*Description*: {p.description}",
        ]

        if missing_notes:
            ans_parts.append(f"\n*Note on missing data*: {'; '.join(missing_notes)}.")

        return AssistantAskResponse(
            question=raw_question,
            answer="\n".join(ans_parts),
            grounded=True,
            structured_evidence=evidence,
            referenced_products=[ProductResponse.model_validate(p)],
            missing_data_notes="; ".join(missing_notes) if missing_notes else None,
            used_llm=False,
        )

    def _handle_general_retrieval_query(self, query: str) -> AssistantAskResponse:
        from app.api.schemas import SearchRequest

        search_req = SearchRequest(query=query, top_k=3, search_mode="hybrid")
        search_res = self.hybrid_engine.search(search_req)

        if not search_res.results:
            return AssistantAskResponse(
                question=query,
                answer="I could not find any products in our catalogue that directly answer your inquiry. Please try searching with specific categories like desks, sofas, tables, or chairs.",
                grounded=True,
                structured_evidence=[],
                referenced_products=[],
                missing_data_notes="No matching products retrieved.",
                used_llm=False,
            )

        evidence = []
        referenced = []
        answer_bullets = []

        for item in search_res.results:
            p = item.product
            referenced.append(p)
            evidence.append(
                AssistantFactItem(
                    product_id=p.product_id,
                    title=p.title,
                    attribute="price",
                    value=f"₹{p.price:,.0f}",
                )
            )
            if p.material:
                evidence.append(
                    AssistantFactItem(
                        product_id=p.product_id,
                        title=p.title,
                        attribute="material",
                        value=p.material,
                    )
                )

            dim_info = f", {p.width} cm width" if p.width else ""
            mat_info = f", crafted from {p.material}" if p.material else ""
            answer_bullets.append(
                f"- **{p.title}** ({p.product_id}) — **₹{p.price:,.0f}**: {item.match_explanation} ({p.style.capitalize() if p.style else 'Standard'}{mat_info}{dim_info})."
            )

        final_answer = (
            f'Based on verified catalogue records, here are the top matching options for **"{query}"**:\n\n'
            + "\n".join(answer_bullets)
        )

        return AssistantAskResponse(
            question=query,
            answer=final_answer,
            grounded=True,
            structured_evidence=evidence,
            referenced_products=referenced,
            missing_data_notes=None,
            used_llm=False,
        )
