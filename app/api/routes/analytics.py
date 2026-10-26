import json

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    EvaluationResponse,
    MethodComparison,
    MetricSet,
    QueryEvaluationResult,
)
from app.config import settings
from app.evaluation.run import run_evaluation

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/search-evaluation", response_model=EvaluationResponse)
def get_search_evaluation():
    cache_file = settings.INDEX_CACHE_DIR / "evaluation_results.json"

    if not cache_file.exists():
        try:
            data = run_evaluation()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate evaluation: {e!s}")
    else:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read evaluation results: {e!s}")

    comp = data["method_comparison"]
    comparison = MethodComparison(
        keyword=MetricSet(**comp["keyword"]),
        semantic=MetricSet(**comp["semantic"]),
        hybrid=MetricSet(**comp["hybrid"]),
    )

    query_details = [QueryEvaluationResult(**q) for q in data.get("query_details", [])]

    return EvaluationResponse(
        total_queries=data.get("total_queries", 0),
        comparison=comparison,
        query_details=query_details,
        analysis_notes=data.get("analysis_notes", ""),
        timestamp=data.get("timestamp", ""),
    )
