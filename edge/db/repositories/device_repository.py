from edge.domain.models.device import Device
from edge.domain.enums.device_type import DeviceType
from edge.domain.enums.device_status import DeviceStatus
from edge.domain.repositories.device_repository import DeviceRepository
from edge.db.base import SessionLocal
from edge.db.orm.device import DeviceORM


class SqlDeviceRepository(DeviceRepository):
    def get_by_ip(self, ip: str) -> Device | None:
        with SessionLocal() as session:
            row = session.query(DeviceORM).filter(DeviceORM.ip == ip).first()
            return self._to_domain(row) if row else None

    def save(self, device: Device) -> None:
        with SessionLocal() as session:
            row = session.query(DeviceORM).filter(DeviceORM.ip == device.ip).first()
            if row is None:
                row = self._to_orm(device)
                session.add(row)
            else:
                self._update_orm(row, device)
            session.commit()

    def get_all(self) -> list[Device]:
        with SessionLocal() as session:
            rows = session.query(DeviceORM).all()
            return [self._to_domain(row) for row in rows]

    def _to_orm(self, device: Device) -> DeviceORM:
        return DeviceORM(
            ip=device.ip,
            mac=device.mac,
            device_type=device.device_type.value,
            status=device.status.value,
            vendor=device.vendor,
            first_seen=device.first_seen,
            last_seen=device.last_seen,
        )

    def _update_orm(self, row: DeviceORM, device: Device) -> None:
        row.mac = device.mac
        row.device_type = device.device_type.value
        row.status = device.status.value
        row.vendor = device.vendor
        row.last_seen = device.last_seen

    def _to_domain(self, row: DeviceORM) -> Device:
        return Device(
            ip=row.ip,
            mac=row.mac,
            device_type=DeviceType(row.device_type),
            status=DeviceStatus(row.status),
            vendor=row.vendor,
            first_seen=row.first_seen,
            last_seen=row.last_seen,
            peers=[],
        )