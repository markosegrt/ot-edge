from fastapi import APIRouter, HTTPException

from edge.api.controllers.correlation_controller import (
    CorrelationController,
    CorrelationContextResponse,
)

router = APIRouter(prefix="/api", tags=["correlation"])
controller = CorrelationController()


@router.get("/alarms/{alarm_id}/context", response_model=CorrelationContextResponse)
def get_correlation_context(alarm_id: int) -> CorrelationContextResponse:
    context = controller.get_context(alarm_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Alarm nije pronadjen")
    return context