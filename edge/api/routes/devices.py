from fastapi import APIRouter

from edge.api.controllers.devices_controller import DevicesController, DeviceResponse

router = APIRouter(prefix="/api", tags=["devices"])
controller = DevicesController()


@router.get("/devices", response_model=list[DeviceResponse])
def get_devices() -> list[DeviceResponse]:
    return controller.list_devices()