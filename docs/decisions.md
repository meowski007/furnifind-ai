# FurniFind AI — Architecture Decision Records (ADRs)

This document captures the key architectural choices, trade-offs, and alternatives considered during the design of FurniFind AI.

---

## ADR-001: Relational Database & ORM Strategy

### Context
The application requires reliable transactional storage for products, prices, and dimensions, with support for filtering and structured comparisons.

### Decision
Use **SQLAlchemy 2.0 with SQLite** for local zero-configuration development, with support for **PostgreSQL** in production/Docker. Synchronous database sessions are used within FastAPI's threadpool (`def` handlers).

### Alternatives Considered
- *MongoDB / Document Store*: Rejected because furniture specifications require strict schema validation, dimensional typing, and consistent comparison queries.
- *Async SQLite (`aiosqlite`)*: Explored but replaced with standard SQLAlchemy session pools due to known event loop thread-safety issues in Windows developer environments.

### Trade-offs
SQLite provides instant setup without running external database daemons. For large-scale production (millions of SKUs), PostgreSQL with `pgvector` or Elasticsearch would be the natural migration path.

---

## ADR-002: Hybrid Retrieval (Lexical + Semantic) Strategy

### Context
E-commerce search must understand both conceptual natural language descriptions ("cozy couch for small studio") and exact SKU specifications ("oak desk 115 cm").

### Decision
Implement **Dual-Stream Hybrid Retrieval**:
1. Okapi BM25 for lexical token matching and rare term weighting.
2. `all-MiniLM-L6-v2` for dense semantic vector representation.
3. Weighted blend scoring with configurable $\alpha$ parameter.

### Alternatives Considered
- *Pure Keyword Search (BM25 only)*: Fast and exact, but high empty result rate on synonyms ("workstation" -> desk).
- *Pure Dense Semantic Search*: High recall on descriptive queries, but prone to semantic drift and poor precision on exact part numbers or rare materials.

---

## ADR-003: Hard Constraint Enforcement vs Soft Scoring

### Context
Users frequently search with strict physical or financial boundaries (e.g. "budget ₹15,000", "width below 120 cm").

### Decision
Enforce hard constraints as mandatory pre-filters or pruning rules before final ranking. Products violating maximum budget or maximum width are strictly filtered out, regardless of how high their semantic description score might be.

### Trade-offs
A customer with a 115 cm alcove cannot use a 140 cm desk, even if the desk is a 99% aesthetic match. Hard filtering prevents returns and customer dissatisfaction.

---

## ADR-004: In-Memory / File-Backed Vector Cache vs External Vector DB

### Context
Vector retrieval needs to be fast and responsive on a standard developer laptop without requiring GPU servers or paid vector database subscriptions (Pinecone, Qdrant).

### Decision
Use precomputed NumPy arrays (`np.ndarray`) cached to disk (`.cache/text_emb_*.npy`) with MD5 catalogue content hashing. Query embeddings are calculated on CPU in 15 ms and cosine similarities computed via vectorized matrix dot products.

### Alternatives Considered
- *Hosted Pinecone / Weaviate*: Rejected to prevent paid API credentials from being a prerequisite to running the project.
- *FAISS*: Viable for large catalogues; for catalogues of thousands of items, direct NumPy vector operations are faster, dependency-free, and cross-platform stable.

---

## ADR-005: Deterministic Execution for Superlative E-Commerce Comparisons

### Context
When answering questions like "Which desk is the narrowest and under ₹15,000?", LLMs frequently hallucinate numbers or miscalculate inequalities.

### Decision
Implement a deterministic question classifier in Python/SQL that computes minimums, maximums, and price comparisons directly from database records. An LLM is only used for linguistic synthesis, never for numerical computation.

### Trade-offs
Ensures 100% mathematical fidelity. The assistant never invents unrecorded dimensions or misquotes prices.
