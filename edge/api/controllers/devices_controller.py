from datetime import datetime

from pydantic import BaseModel

from edge.db.repositories.device_repository import SqlDeviceRepository


class DeviceResponse(BaseModel):
    ip: str
    mac: str | None
    device_type: str
    status: str
    vendor: str | None
    first_seen: datetime
    last_seen: datetime


class DevicesController:
    def __init__(self):
        self.device_repository = SqlDeviceRepository()

    def list_devices(self) -> list[DeviceResponse]:
        devices = self.device_repository.get_all()
        return [
            DeviceResponse(
                ip=d.ip,
                mac=d.mac,
                device_type=d.device_type.value,
                status=d.status.value,
                vendor=d.vendor,
                first_seen=d.first_seen,
                last_seen=d.last_seen,
            )
            for d in devices
        ]