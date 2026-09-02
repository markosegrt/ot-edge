from fastapi import APIRouter

from edge.api.controllers.alarms_controller import AlarmsController, AlertResponse

router = APIRouter(prefix="/api", tags=["alarms"])
controller = AlarmsController()


@router.get("/alarms", response_model=list[AlertResponse])
def get_alarms() -> list[AlertResponse]:
    return controller.list_alarms()