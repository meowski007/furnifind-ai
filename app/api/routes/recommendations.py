from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import RecommendationRequest, RecommendationResponse
from app.core.database import get_db
from app.services.registry import registry

router = APIRouter(prefix="/api/v1/recommendations", tags=["Recommendations"])


@router.post("", response_model=RecommendationResponse)
def get_recommendations(req: RecommendationRequest, db: Session = Depends(get_db)):
    if not registry.is_initialized:
        registry.initialize(db)

    if not registry.recommender:
        raise HTTPException(status_code=503, detail="Recommendation engine is not initialized.")

    return registry.recommender.recommend(req)
