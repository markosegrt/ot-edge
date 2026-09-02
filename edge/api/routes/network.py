from fastapi import APIRouter

from edge.api.controllers.network_controller import NetworkController, NetworkResponse

router = APIRouter(prefix="/api", tags=["network"])
controller = NetworkController()


@router.get("/network", response_model=NetworkResponse)
def get_network() -> NetworkResponse:
    return controller.get_network()