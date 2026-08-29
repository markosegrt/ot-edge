from datetime import datetime, timezone

from edge.domain.enums.device_status import DeviceStatus
from edge.domain.enums.device_type import DeviceType
from edge.domain.models.baseline_device import BaselineDevice
from edge.domain.models.device import Device
from edge.domain.models.flow import Flow
from edge.domain.repositories.device_repository import DeviceRepository
from edge.domain.services.inventory_service import InventoryService
from edge.helpers.device_classifier import classify_by_ports


class BasicInventoryService(InventoryService):
    def __init__(self, repository: DeviceRepository, baseline: dict[str, BaselineDevice]):
        self.repository = repository
        self.baseline = baseline

    def observe_flow(self, flow: Flow) -> None:
        now = datetime.now(timezone.utc)
        self._observe_device(flow.source_ip, listening_port=None, seen_at=now)
        self._observe_device(flow.destination_ip, listening_port=flow.destination_port, seen_at=now)

    def _observe_device(self, ip: str, listening_port: int | None, seen_at: datetime) -> None:
        device = self.repository.get_by_ip(ip)

        if device is None:
            device = self._create_device(ip, listening_port, seen_at)
        else:
            device.last_seen = seen_at
            if listening_port is not None and device.device_type == DeviceType.UNKNOWN:
                device.device_type = classify_by_ports({listening_port})

        self.repository.save(device)

    def _create_device(self, ip: str, listening_port: int | None, seen_at: datetime) -> Device:
        known = self.baseline.get(ip)

        if known is not None:
            return Device(
                ip=ip,
                mac=None,
                device_type=known.device_type,
                status=DeviceStatus.KNOWN,
                vendor=None,
                first_seen=seen_at,
                last_seen=seen_at,
                peers=[],
            )

        device_type = DeviceType.UNKNOWN
        if listening_port is not None:
            device_type = classify_by_ports({listening_port})

        return Device(
            ip=ip,
            mac=None,
            device_type=device_type,
            status=DeviceStatus.NEW,
            vendor=None,
            first_seen=seen_at,
            last_seen=seen_at,
            peers=[],
        )