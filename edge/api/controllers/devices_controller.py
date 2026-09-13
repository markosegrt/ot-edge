from datetime import datetime

from pydantic import BaseModel

from edge.db.repositories.device_repository import SqlDeviceRepository
from edge.db.repositories.baseline_repository import SqlBaselineRepository


class DeviceResponse(BaseModel):
    ip: str
    mac: str | None
    device_type: str
    status: str
    vendor: str | None
    name: str | None
    first_seen: datetime
    last_seen: datetime


class DevicesController:
    def __init__(self):
        self.device_repository = SqlDeviceRepository()
        self.baseline_repository = SqlBaselineRepository()

    def list_devices(self) -> list[DeviceResponse]:
        devices = self.device_repository.get_all()
        # Baseline po IP-u — za tip i ime poznatih uredjaja.
        baseline = {b.ip: b for b in self.baseline_repository.get_all()}

        result = []
        for d in devices:
            known = baseline.get(d.ip)
            # Ako je uredjaj u baseline-u, koristi NJEGOV tip i ime (operater
            # ga je opisao). Status OSTAJE iz devices (NEW/KNOWN se ne dira).
            if known is not None:
                device_type = known.device_type.value
                name = known.name
            else:
                device_type = d.device_type.value
                name = None

            result.append(
                DeviceResponse(
                    ip=d.ip,
                    mac=d.mac,
                    device_type=device_type,
                    status=d.status.value,
                    vendor=d.vendor,
                    name=name,
                    first_seen=d.first_seen,
                    last_seen=d.last_seen,
                )
            )
        return result