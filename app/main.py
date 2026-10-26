from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    analytics,
    assistant,
    health,
    products,
    recommendations,
    search,
)
from app.config import settings
from app.core.database import SessionLocal, init_db
from app.core.logging import logger
from app.services.registry import registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}...")
    init_db()
    with SessionLocal() as db:
        registry.initialize(db)
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title="FurniFind AI — Multimodal Furniture Search & Recommendation Engine",
    description=(
        "Production-style e-commerce discovery engine for furniture featuring natural language search, "
        "BM25 + Semantic hybrid retrieval, multimodal image similarity search, explainable content-based "
        "recommendations, and a grounded RAG shopping assistant."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local images directory for static image serving
images_dir = settings.DATA_DIR / "images"
images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=str(images_dir)), name="images")

# Include API Routers
app.include_router(health.router)
app.include_router(products.router)
app.include_router(search.router)
app.include_router(recommendations.router)
app.include_router(assistant.router)
app.include_router(analytics.router)


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")
