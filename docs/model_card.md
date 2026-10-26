# FurniFind AI — Model Card & Algorithmic Inventory

This document distinguishes pretrained deep learning models, locally implemented deterministic algorithms, and external LLM services in FurniFind AI.

---

## 1. Pretrained Neural Models

### A. Sentence Embeddings: `all-MiniLM-L6-v2`
- **Developer**: Hugging Face / Sentence Transformers (Reimers & Gurevych)
- **Architecture**: 6-layer BERT-Mini transformer
- **Parameters**: 22.7 Million
- **Embedding Dimension**: 384
- **Intended Use**: Dense sentence and paragraph semantic representation.
- **Latency on CPU**: ~15-25 ms per query.
- **Local Caching**: Embeddings for catalogue products are cached in `.cache/text_emb_all-MiniLM-L6-v2_{hash}.npy` so recomputation on requests is avoided.
- **Offline / Failure Fallback**: Gracefully falls back to TF-IDF n-gram vectorizer with L2 normalization if offline or un-downloaded.

### B. Vision Encoder: `clip-ViT-B-32`
- **Developer**: OpenAI
- **Architecture**: Vision Transformer (ViT-B/32) image encoder
- **Parameters**: ~151 Million (vision backbone ~87M)
- **Embedding Dimension**: 512
- **Intended Use**: Zero-shot image feature extraction for visual similarity discovery.
- **Fallback Implementation**: When CLIP model weights are offline, FurniFind AI uses a deterministic Computer Vision Color & Spatial Histogram Extractor (48-bin RGB color distribution + 4x4 spatial pyramid color grid) to extract and compare real image features without external network dependencies.

---

## 2. Locally Implemented Algorithms

### A. Okapi BM25 Keyword Engine
- **Type**: Classical probabilistic Information Retrieval
- **Implementation**: Pure Python (`app/services/search/keyword_search.py`)
- **Parameters**: $k_1 = 1.5, b = 0.75$
- **Weighting**: Multi-field document representation:
  - Title ($3\times$), Category ($2\times$), Material ($2\times$), Style ($2\times$), Description ($1\times$).
- **Features**: Sub-linear term frequency saturation, document length normalization, and token matching explanation extraction.

### B. Content-Based Recommendation Engine
- **Type**: Multi-attribute affinity vector scoring with diversity re-ranking
- **Implementation**: Pure Python (`app/services/recommendations/engine.py`)
- **Scoring Function**:
  $$\text{Score}(p) = w_{\text{cat}} \cdot S_{\text{cat}} + w_{\text{style}} \cdot S_{\text{style}} + w_{\text{mat}} \cdot S_{\text{mat}} + w_{\text{col}} \cdot S_{\text{col}} + w_{\text{price}} \cdot S_{\text{price}}$$
- **Interaction Signal Weighting**:
  - Saved Products: $2.0\times$ weight boost.
  - Viewed Products: $1.0\times$ weight boost.
  - Stated Preferences: $3.0\times$ weight boost.
- **Cold-Start Strategy**: Curates diverse anchor products across distinct categories for new users.
- **Diversity Re-Ranking**: Caps recommendations to a maximum per category to prevent homogenous listings.

---

## 3. External LLM Integration & Guardrails

- **Provider**: Optional OpenAI / Gemini compatible API (configurable via `LLM_PROVIDER` and `LLM_API_KEY`).
- **Default State**: `LLM_PROVIDER=none` (operates 100% locally with zero paid API requirements).
- **Deterministic RAG Engine**:
  - Handles numerical and superlative questions (`narrowest desk under 15000`) using exact Python/SQL data filters.
  - Answers specific product inquiries directly from catalogue records.
  - Formulates structured evidence citations linking directly to verified catalogue fields.
- **Guardrails**:
  - Rejects prompt injection patterns.
  - Sanitizes user input.
  - Rejects out-of-scope non-furniture queries.
  - Discloses missing catalogue fields explicitly.
