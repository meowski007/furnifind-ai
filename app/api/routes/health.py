from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database_connected": db_ok,
        "models": {
            "text_embedding": settings.EMBEDDING_MODEL_NAME,
            "vision_encoder": settings.VISION_MODEL_NAME,
            "llm_provider": settings.LLM_PROVIDER,
        },
    }
