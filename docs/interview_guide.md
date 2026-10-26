# FurniFind AI — Wayfair Technical Interview Guide & Explanations

This guide explains FurniFind AI's core components in clear, professional language, followed by **ten technical interview questions** with concise, code-grounded answers.

---

## Part 1: Major Architecture Components

### 1. Query Understanding & Filter Extraction (`app/services/search/query_parser.py`)
- **What it does**: Parses natural language queries (e.g. *"modern oak desk under ₹15000, width below 120cm"*) into structured filters (`category: "desks"`, `max_price: 15000`, `max_width_cm: 120`, `material: "oak"`).
- **Why it exists**: Users rarely use dropdown filters when they can type their intent directly. Extracting constraints allows e-commerce platforms to enforce hard business logic.
- **How it works**: Uses regex and lexical rules to isolate dimensions, price ceilings, and categories. Cleans out constraint tokens to produce a residual query for semantic matching.
- **Alternatives considered**: Zero-shot LLM parsing. Rejected for primary search path because regex runs in <0.2 ms with 0 API cost and zero network failure points.
- **Limitations**: Complex compound clauses with dependent conditions may require semantic semantic parsing.
- **How it is tested**: `tests/test_query_parser.py` validates price extraction, dimension extraction, synonym resolution, and negative cases.

### 2. Hybrid Retrieval Engine (`app/services/search/hybrid_search.py`)
- **What it does**: Combines Okapi BM25 keyword retrieval with dense Sentence Transformer vector embeddings.
- **Why it exists**: Keyword search fails on synonyms (*"couch"* vs *"sofa"*). Pure semantic search fails on specific product numbers, dimensions, and hard budgets.
- **How it works**: Prunes candidates violating hard filters. Computes normalized BM25 score and dense cosine similarity, blending them via $(1 - \alpha) \cdot S_{\text{kw}} + \alpha \cdot S_{\text{sem}}$.
- **Alternatives considered**: Reciprocal Rank Fusion (RRF). RRF is also viable, but linear score interpolation provides continuous weighting control.
- **Limitations**: In small catalogues, dense embeddings can exhibit semantic drift.
- **How it is tested**: Evaluated in `app/evaluation/run.py` and unit tested in `tests/test_search_retrieval.py`.

### 3. Multimodal Image Search (`app/services/vision/image_search.py`)
- **What it does**: Allows customers to upload a furniture photo and retrieves visually similar items from the catalogue.
- **Why it exists**: Furnishings have aesthetic qualities (curves, textures, silhouettes) that customers cannot easily express in words.
- **How it works**: Decodes image with Pillow, generates embeddings via CLIP ViT-B-32 (or a deterministic 3D color histogram and spatial pyramid grid fallback), and computes cosine similarity with pre-indexed catalogue images.
- **Alternatives considered**: Deep autoencoders or commercial visual search APIs. Pretrained CLIP provides superior zero-shot vision-language alignment.
- **Limitations**: Highly cluttered rooms require object segmentation (cropping just the chair before embedding).
- **How it is tested**: `tests/test_image_search.py` validates invalid files, dimensions, corrupted buffers, and feature extraction.

### 4. Content-Based Recommendation Engine (`app/services/recommendations/engine.py`)
- **What it does**: Suggests personalized furniture based on stated customer preferences and interaction history (viewed and saved products).
- **Why it exists**: Reduces decision fatigue and aids discovery of complementary catalogue inventory.
- **How it works**: Constructs user affinity profiles across style, material, category, and budget. Weights saved items ($2.0\times$) higher than viewed items ($1.0\times$). Implements cold-start onboarding and diversity re-ranking.
- **Alternatives considered**: Collaborative filtering. Collaborative filtering requires millions of user-item matrix interactions; content-based filtering functions effectively with zero user history.
- **Limitations**: Does not model item-to-item co-purchase probabilities.
- **How it is tested**: `tests/test_recommendations.py` tests cold-start diversification, preference filtering, and interaction boosting.

### 5. Grounded RAG Shopping Assistant (`app/services/assistant/rag_engine.py`)
- **What it does**: Answers customer questions about furniture dimensions, prices, and comparisons with zero hallucinated specs.
- **Why it exists**: Factual errors in retail (wrong dimensions or prices) lead to returns, bad customer reviews, and chargebacks.
- **How it works**: Classifies query intent. Computes numerical superlatives (*"narrowest desk"*, *"cheapest chair"*) deterministically via Python/SQL. Generates structured fact citations.
- **Alternatives considered**: Asking an LLM to remember and compare dimensions from its training weights. Rejected due to extreme hallucination rates.
- **Limitations**: Restricted to furniture domain queries.
- **How it is tested**: `tests/test_assistant.py` checks superlatives, missing attribute disclosure, prompt injection defense, and off-topic rejection.

---

## Part 2: Ten Technical Interview Questions & Answers

### Q1: "Why did you implement a Hybrid search engine rather than relying solely on Sentence Transformers or Vector Embeddings?"
> **Answer**:  
> In e-commerce information retrieval, dense embeddings excel at conceptual semantic understanding (e.g., mapping *"workstation"* to *"desk"*), but they suffer from **semantic drift** on specific keywords, SKU codes, and hard constraints. For example, a 140 cm desk might have high cosine similarity to a query for a *"100 cm desk"* because both are modern wooden desks. BM25 provides exact token matching and term frequency saturation, while dense vectors provide semantic recall. Blending both and enforcing hard constraint pre-filtering yields the highest precision and prevents returning invalid products to the customer.

### Q2: "How does your system enforce hard constraints like budget or width, and why not let the vector embedding handle them?"
> **Answer**:  
> Vector embeddings map text into continuous geometric spaces where numbers are treated as linguistic tokens, not mathematical values. A vector model has no native concept of the mathematical inequality $\text{price} \le 15000$. In `app/services/search/query_parser.py`, our deterministic regex pipeline extracts exact numeric constraints into typed fields (`max_price: float`, `max_width_cm: float`). Then, in `app/services/search/hybrid_search.py`, `apply_hard_filters` evaluates every candidate against these constraints before final ranking. If an item exceeds the budget or width limit, it is eliminated.

### Q3: "How do you evaluate search quality, and what metrics did you track?"
> **Answer**:  
> We built a reproducible benchmark in `app/evaluation/run.py` evaluated over a curated ground-truth test collection (`data/evaluation_queries.json`). We measure:
> 1. **Precision@5**: Percentage of top-5 results that are relevant.
> 2. **Recall@5**: Percentage of all relevant items captured in top-5.
> 3. **NDCG@5**: Normalized Discounted Cumulative Gain, evaluating ranking quality by rewarding relevant items placed at higher positions.
> 4. **MRR**: Mean Reciprocal Rank of the first relevant result.
> 5. **Empty Result Rate**: Percentage of queries returning zero results.
> On our test set, BM25 achieved strong precision on exact queries but had a 33.3% empty result rate on synonyms. Dense embeddings lowered empty results to 25.0%, and Hybrid retrieval combined both strengths while enforcing constraints.

### Q4: "How does your multimodal image search work, and how do you handle cases where heavy deep-learning models cannot run?"
> **Answer**:  
> In `app/services/vision/image_search.py`, we implement a production pipeline that accepts image uploads, validates MIME types (`JPEG`, `PNG`, `WEBP`), verifies image dimensions, and extracts a normalized feature vector. We support `clip-ViT-B-32` from OpenAI for joint visual-linguistic embeddings. To ensure high availability and zero-crash resiliency on offline or resource-constrained environments, we implemented a deterministic Computer Vision fallback using 48-bin RGB color histograms and a 4x4 spatial pyramid color grid. This ensures genuine visual comparison based on actual pixel data without returning random mock results.

### Q5: "How does your recommendation engine handle the cold-start problem for a first-time visitor?"
> **Answer**:  
> In `app/services/recommendations/engine.py`, the `recommend` method detects when a user has no viewed products, no saved items, and no stated preferences (`is_cold_start = True`). Instead of returning an empty state or arbitrary items, it executes `_cold_start_recommendations`, which curates a diversified discovery showcase by selecting top-rated representative anchor products across distinct categories (desks, chairs, sofas, tables, beds, storage). As soon as the customer clicks or saves an item, interaction weights ($1.0\times$ for views, $2.0\times$ for saves) immediately pivot recommendations toward their observed taste.

### Q6: "Why did you choose deterministic Python/SQL logic over an LLM for numerical comparisons in your Shopping Assistant?"
> **Answer**:  
> LLMs are autoregressive next-token predictors; they do not perform arithmetic or relational comparisons reliably from raw weights. Asking an LLM *"Which desk is the narrowest under ₹15,000?"* frequently results in hallucinations where the model invents dimensions or misidentifies the minimum. In `app/services/assistant/rag_engine.py`, `_handle_superlative_query` parses the constraint, runs exact relational filtering on verified catalogue records, and returns the mathematically verified minimum. The assistant cites the exact dimension (`105 cm`) and price (`₹11,999`), guaranteeing 100% factual accuracy.

### Q7: "How did you protect the shopping assistant against prompt injection and jailbreaking?"
> **Answer**:  
> In `app/services/assistant/guardrails.py`, incoming prompts pass through `AssistantGuardrails.sanitize_and_check_injection`. We check for adversarial patterns such as *"ignore previous instructions"*, *"reveal system prompt"*, and script tags. If flagged, the query is rejected before reaching model inference. Furthermore, the assistant enforces domain boundaries: queries unrelated to home furnishings or catalogue specifications are politely declined, preventing misuse of LLM resources.

### Q8: "How is vector caching handled to ensure low query latency?"
> **Answer**:  
> Recomputing dense embeddings on every request causes unacceptable latency ($>500$ ms). In `app/services/search/semantic_search.py`, we compute an MD5 hash of the catalogue products. Embeddings are generated once during ingestion and persisted as a `.npy` matrix in `.cache/text_emb_{model}_{hash}.npy`. On subsequent requests and server restarts, the precomputed matrix is loaded in $<5$ ms. During search, only the single incoming user query vector is calculated on CPU (~15 ms), followed by a vectorized matrix dot product that ranks all candidates in $<2$ ms.

### Q9: "What database architecture did you use, and how would you scale this to millions of SKUs at Wayfair scale?"
> **Answer**:  
> For this portfolio project, we used SQLAlchemy 2.0 with SQLite for zero-setup local reproducibility, containerized with PostgreSQL for production parity. To scale to Wayfair's catalogue of over 30 million products:
> 1. Migrate vector indexing to **HNSW** (Hierarchical Navigable Small World) graphs using `pgvector` or a dedicated distributed search cluster (e.g., Elasticsearch / OpenSearch with k-NN).
> 2. Partition the catalogue across horizontal shards based on root department (`Furniture`, `Lighting`, `Décor`).
> 3. Implement Redis caching for frequent search query candidate sets.
> 4. Offload embedding generation to an asynchronous worker queue (Celery / Kafka) upon catalogue SKU updates.

### Q10: "How did you ensure testability across the full stack?"
> **Answer**:  
> Testing is built as a core quality gate:
> - **Backend**: 32 unit and integration tests in `pytest` covering query parsing, constraint validation, BM25 retrieval, semantic scoring, cold-start recommendations, image upload validation, RAG superlatives, and FastAPI endpoints via `TestClient`.
> - **Frontend**: Vitest unit tests verifying state, math, and filter validation; TypeScript strict type checking (`tsc --noEmit`); and Vite production bundling.
> - **Linting**: Ruff enforces Python standards and isort import ordering.
> - **CI/CD**: GitHub Actions workflow (`.github/workflows/ci.yml`) runs linting, ingestion, tests, benchmark evaluation, and frontend build on every pull request.
