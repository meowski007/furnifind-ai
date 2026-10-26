from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import AssistantAskRequest, AssistantAskResponse
from app.core.database import get_db
from app.services.registry import registry

router = APIRouter(prefix="/api/v1/assistant", tags=["Assistant"])


@router.post("/ask", response_model=AssistantAskResponse)
def ask_assistant(req: AssistantAskRequest, db: Session = Depends(get_db)):
    if not registry.is_initialized:
        registry.initialize(db)

    if not registry.assistant:
        raise HTTPException(
            status_code=503, detail="Assistant engine is not initialized."
        )

    return registry.assistant.answer_question(req)
