import hashlib
import json
from pathlib import Path

import numpy as np

from app.config import settings
from app.core.logging import logger
from app.models.product import Product


class SemanticSearchEngine:
    """Pretrained sentence embedding retriever with caching and graceful offline fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: Path | None = None):
        self.model_name = model_name
        self.cache_dir = cache_dir or settings.INDEX_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.products: list[Product] = []
        self.product_ids: list[str] = []
        self.embeddings: np.ndarray | None = None
        self._model = None
        self._is_transformer: bool = False
        self._tfidf_fallback = None

    def _get_catalogue_hash(self, products: list[Product]) -> str:
        s = "".join(
            f"{p.product_id}_{p.title}_{p.category}_{p.material}_{p.style}" for p in products
        )
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def _init_model(self):
        if self._model is not None or self._tfidf_fallback is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            # Try loading cached local files first to avoid network timeout
            try:
                self._model = SentenceTransformer(self.model_name, local_files_only=True)
                self._is_transformer = True
                logger.info(f"Loaded local SentenceTransformer: {self.model_name}")
                return
            except Exception:
                pass

            logger.info(f"Loading SentenceTransformer: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self._is_transformer = True
            logger.info("SentenceTransformer successfully loaded.")
        except Exception as e:
            logger.warning(
                f"Could not load SentenceTransformer ({e!s}). Falling back to TF-IDF semantic vector space."
            )
            from sklearn.feature_extraction.text import TfidfVectorizer

            self._tfidf_fallback = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
            self._is_transformer = False

    def fit(self, products: list[Product], force_refresh: bool = False):
        self.products = products
        self.product_ids = [p.product_id for p in products]

        if not products:
            self.embeddings = None
            return

        cat_hash = self._get_catalogue_hash(products)
        emb_file = self.cache_dir / f"text_emb_{self.model_name}_{cat_hash}.npy"
        meta_file = self.cache_dir / f"text_meta_{self.model_name}_{cat_hash}.json"

        # Check cache
        if not force_refresh and emb_file.exists() and meta_file.exists():
            try:
                self.embeddings = np.load(emb_file)
                logger.info(f"Loaded {len(self.embeddings)} cached text embeddings from {emb_file}")
                return
            except Exception as e:
                logger.warning(f"Failed loading cached embeddings: {e}, recalculating.")

        self._init_model()

        # Build rich text descriptions for semantic embedding
        texts = []
        for p in products:
            parts = [
                f"{p.title}.",
                p.description,
                f"Category: {p.category}.",
                f"Style: {p.style or 'contemporary'}." if p.style else "",
                f"Material: {p.material}." if p.material else "",
                f"Colour: {p.colour}." if p.colour else "",
            ]
            full_text = " ".join(part for part in parts if part)
            texts.append(full_text)

        if self._is_transformer and self._model is not None:
            raw_embs = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            self.embeddings = np.array(raw_embs, dtype=np.float32)
        else:
            if self._tfidf_fallback is None:
                from sklearn.feature_extraction.text import TfidfVectorizer

                self._tfidf_fallback = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
            sparse_matrix = self._tfidf_fallback.fit_transform(texts)
            self.embeddings = sparse_matrix.toarray().astype(np.float32)
            # L2 normalize
            norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.embeddings = self.embeddings / norms

        try:
            np.save(emb_file, self.embeddings)
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump({"catalogue_hash": cat_hash, "count": len(products)}, f)
            logger.info(f"Saved {len(self.embeddings)} embeddings to cache at {emb_file}")
        except Exception as e:
            logger.warning(f"Failed to persist embeddings cache: {e}")

    def search(self, query: str, top_k: int = 20) -> list[tuple[Product, float]]:
        if self.embeddings is None or len(self.products) == 0 or not query.strip():
            return []

        self._init_model()

        if self._is_transformer and self._model is not None:
            q_emb = self._model.encode([query], show_progress_bar=False, normalize_embeddings=True)[
                0
            ]
        else:
            sparse_q = self._tfidf_fallback.transform([query])
            q_emb = sparse_q.toarray().astype(np.float32)[0]
            norm = np.linalg.norm(q_emb)
            if norm > 0:
                q_emb = q_emb / norm

        # Cosine similarity (already unit vectors)
        sims = np.dot(self.embeddings, q_emb)

        # Scale sims to [0, 1] range
        sims = np.clip(sims, 0.0, 1.0)

        # Rank indices
        top_indices = np.argsort(sims)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score > 0.01:
                results.append((self.products[idx], score))

        return results
