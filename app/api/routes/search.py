import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import (
    ImageSearchResponse,
    ImageSearchResultItem,
    ProductResponse,
    SearchRequest,
    SearchResponse,
)
from app.core.database import get_db
from app.core.logging import logger
from app.services.registry import registry
from app.services.vision.image_search import ImageValidationError

router = APIRouter(prefix="/api/v1/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
def search_products(request: SearchRequest, db: Session = Depends(get_db)):
    if not registry.is_initialized:
        registry.initialize(db)

    if not registry.hybrid_engine:
        raise HTTPException(status_code=503, detail="Search engine is not initialized.")

    return registry.hybrid_engine.search(request)


@router.post("/image", response_model=ImageSearchResponse)
async def search_by_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    start_time = time.perf_counter()

    if not registry.is_initialized:
        registry.initialize(db)

    if not registry.image_engine:
        raise HTTPException(
            status_code=503, detail="Image search engine is not initialized."
        )

    try:
        content_bytes = await file.read()
        pil_image = registry.image_engine.validate_upload(
            content_bytes, filename=file.filename
        )
        matches = registry.image_engine.search_by_image(pil_image, top_k=6)

        results = []
        for prod, score in matches:
            explanation = f"Visual appearance and color profile match your uploaded reference ({score:.1%} visual similarity)."
            results.append(
                ImageSearchResultItem(
                    product=ProductResponse.model_validate(prod),
                    similarity_score=round(score, 4),
                    visual_match_explanation=explanation,
                )
            )

        latency = (time.perf_counter() - start_time) * 1000.0

        return ImageSearchResponse(
            total_matches=len(results),
            results=results,
            latency_ms=round(latency, 2),
            encoder_used=registry.image_engine.encoder_name,
        )

    except ImageValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Image search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e!s}")
