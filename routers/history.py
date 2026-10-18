from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_current_user, get_history_service
from schemas import HistoryResponse
from services.history_service import HistoryService

router = APIRouter()


@router.get("", response_model=list[HistoryResponse])
def get_history(
    filter_type: Literal["all", "car", "part"] = "all",
    value: str | None = Query(
        None,
        description="Car number or part name; required for car and part filters",
    ),
    current_user=Depends(get_current_user),
    service: HistoryService = Depends(get_history_service),
) -> list[HistoryResponse]:
    if filter_type != "all":
        if value is None or not value.strip():
            raise HTTPException(
                status_code=400,
                detail="Value is required for this filter.",
            )
        value = value.strip().upper() if filter_type == "car" else value.strip().lower()
    return service.get_history(filter_type, value, current_user.user_id)
