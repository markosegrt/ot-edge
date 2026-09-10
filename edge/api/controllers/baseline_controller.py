from pydantic import BaseModel

from edge.domain.models.baseline_device import BaselineDevice
from edge.domain.enums.device_type import DeviceType
from edge.db.repositories.baseline_repository import SqlBaselineRepository


class BaselineResponse(BaseModel):
    ip: str
    device_type: str
    name: str
    trusted: bool
    can_write: bool


class BaselineWrite(BaseModel):
    ip: str
    device_type: str
    name: str
    trusted: bool = True
    can_write: bool = False


class BaselineController:
    def __init__(self):
        self.repository = SqlBaselineRepository()

    def list_baseline(self) -> list[BaselineResponse]:
        return [self._to_response(d) for d in self.repository.get_all()]

    def create_baseline(self, data: BaselineWrite) -> BaselineResponse:
        device = self._to_domain(data)
        self.repository.create(device)
        return self._to_response(device)

    def update_baseline(self, ip: str, data: BaselineWrite) -> BaselineResponse:
        device = self._to_domain(data)
        self.repository.update(ip, device)
        return self._to_response(device)

    def delete_baseline(self, ip: str) -> None:
        self.repository.delete(ip)

    def _to_domain(self, data: BaselineWrite) -> BaselineDevice:
        return BaselineDevice(
            ip=data.ip,
            device_type=DeviceType(data.device_type),
            name=data.name,
            trusted=data.trusted,
            can_write=data.can_write,
        )

    def _to_response(self, d: BaselineDevice) -> BaselineResponse:
        return BaselineResponse(
            ip=d.ip,
            device_type=d.device_type.value,
            name=d.name,
            trusted=d.trusted,
            can_write=d.can_write,
        )