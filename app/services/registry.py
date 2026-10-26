from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.product import Product
from app.services.assistant.rag_engine import AssistantRAGEngine
from app.services.recommendations.engine import ContentBasedRecommender
from app.services.search.hybrid_search import HybridSearchEngine
from app.services.search.keyword_search import BM25SearchEngine
from app.services.search.semantic_search import SemanticSearchEngine
from app.services.vision.image_search import MultimodalImageSearchEngine


class EngineRegistry:
    def __init__(self):
        self.products: list[Product] = []
        self.keyword_engine: BM25SearchEngine | None = None
        self.semantic_engine: SemanticSearchEngine | None = None
        self.hybrid_engine: HybridSearchEngine | None = None
        self.image_engine: MultimodalImageSearchEngine | None = None
        self.recommender: ContentBasedRecommender | None = None
        self.assistant: AssistantRAGEngine | None = None
        self.is_initialized: bool = False

    def initialize(self, db: Session, force_refresh: bool = False):
        if self.is_initialized and not force_refresh:
            return
        logger.info("Initializing FurniFind AI Engine Registry...")
        self.products = db.query(Product).all()
        if not self.products:
            logger.warning("No products found in database during engine registry initialization.")
            return

        # 1. Keyword search engine
        self.keyword_engine = BM25SearchEngine()
        self.keyword_engine.fit(self.products)

        # 2. Semantic search engine
        self.semantic_engine = SemanticSearchEngine()
        self.semantic_engine.fit(self.products, force_refresh=force_refresh)

        # 3. Hybrid search engine
        self.hybrid_engine = HybridSearchEngine(self.keyword_engine, self.semantic_engine)

        # 4. Multimodal image search engine
        self.image_engine = MultimodalImageSearchEngine()
        self.image_engine.fit(self.products, force_refresh=force_refresh)

        # 5. Recommendation engine
        self.recommender = ContentBasedRecommender(self.products)

        # 6. Assistant RAG engine
        self.assistant = AssistantRAGEngine(self.products, self.hybrid_engine)

        self.is_initialized = True
        logger.info(f"Engine Registry successfully initialized with {len(self.products)} products.")


registry = EngineRegistry()
