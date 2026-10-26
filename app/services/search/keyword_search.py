import math
import re

from app.models.product import Product


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    tokens = re.findall(r"\b[a-z0-9]+\b", text.lower())
    # basic stop words
    stop_words = {
        "a",
        "an",
        "the",
        "in",
        "on",
        "at",
        "for",
        "with",
        "and",
        "or",
        "to",
        "of",
        "is",
        "it",
    }
    return [t for t in tokens if t not in stop_words]


class BM25SearchEngine:
    """Explainable Okapi BM25 keyword search engine for furniture catalog."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.products: list[Product] = []
        self.doc_tokens: list[list[str]] = []
        self.doc_lens: list[int] = []
        self.avg_dl: float = 0.0
        self.doc_freqs: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.n_docs: int = 0

    def fit(self, products: list[Product]):
        self.products = products
        self.n_docs = len(products)
        self.doc_tokens = []
        self.doc_lens = []
        self.doc_freqs = {}

        if self.n_docs == 0:
            return

        for p in products:
            # Weighted multi-field representation
            title_tokens = tokenize(p.title) * 3
            desc_tokens = tokenize(p.description)
            cat_tokens = tokenize(p.category) * 2
            mat_tokens = tokenize(p.material or "") * 2
            style_tokens = tokenize(p.style or "") * 2
            col_tokens = tokenize(p.colour or "") * 2

            all_tokens = (
                title_tokens
                + desc_tokens
                + cat_tokens
                + mat_tokens
                + style_tokens
                + col_tokens
            )
            self.doc_tokens.append(all_tokens)
            self.doc_lens.append(len(all_tokens))

            # Count unique terms in document for IDF
            unique_terms = set(all_tokens)
            for t in unique_terms:
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_dl = sum(self.doc_lens) / max(1, self.n_docs)

        # Precompute IDF
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            # Standard Lucene/BM25 IDF formula
            self.idf[term] = math.log(1.0 + (self.n_docs - freq + 0.5) / (freq + 0.5))

    def search(
        self, query: str, top_k: int = 20
    ) -> list[tuple[Product, float, list[str]]]:
        if not self.products or not query:
            return []

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        scores: list[tuple[int, float, list[str]]] = []

        for idx, doc in enumerate(self.doc_tokens):
            score = 0.0
            doc_len = self.doc_lens[idx]
            matched_terms = []

            # Term counts in document
            term_counts: dict[str, int] = {}
            for t in doc:
                term_counts[t] = term_counts.get(t, 0) + 1

            for q_term in q_tokens:
                if q_term in term_counts:
                    tf = term_counts[q_term]
                    idf_val = self.idf.get(q_term, 0.5)
                    # BM25 term score
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (
                        1.0 - self.b + self.b * (doc_len / self.avg_dl)
                    )
                    term_score = idf_val * (numerator / denominator)
                    score += term_score
                    matched_terms.append(q_term)

            if score > 0:
                scores.append((idx, score, matched_terms))

        scores.sort(key=lambda x: x[1], reverse=True)

        if not scores:
            return []

        max_score = scores[0][1] if scores else 1.0
        results = []
        for idx, raw_score, matched in scores[:top_k]:
            normalized_score = min(1.0, raw_score / max(1.0, max_score))
            results.append((self.products[idx], normalized_score, matched))

        return results
