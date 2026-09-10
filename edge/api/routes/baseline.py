from fastapi import APIRouter

from edge.api.controllers.baseline_controller import (
    BaselineController,
    BaselineResponse,
    BaselineWrite,
)

router = APIRouter(prefix="/api", tags=["baseline"])
controller = BaselineController()


@router.get("/baseline", response_model=list[BaselineResponse])
def get_baseline() -> list[BaselineResponse]:
    return controller.list_baseline()


@router.post("/baseline", response_model=BaselineResponse)
def create_baseline(data: BaselineWrite) -> BaselineResponse:
    return controller.create_baseline(data)


@router.put("/baseline/{ip}", response_model=BaselineResponse)
def update_baseline(ip: str, data: BaselineWrite) -> BaselineResponse:
    return controller.update_baseline(ip, data)


@router.delete("/baseline/{ip}")
def delete_baseline(ip: str) -> dict:
    controller.delete_baseline(ip)
    return {"deleted": ip}