from edge.domain.models.baseline_device import BaselineDevice
from edge.domain.enums.device_type import DeviceType
from edge.domain.repositories.baseline_repository import BaselineRepository
from edge.db.base import SessionLocal
from edge.db.orm.baseline import BaselineDeviceORM


class SqlBaselineRepository(BaselineRepository):
    def get_all(self) -> list[BaselineDevice]:
        with SessionLocal() as session:
            rows = session.query(BaselineDeviceORM).all()
            return [self._to_domain(row) for row in rows]

    def get_by_ip(self, ip: str) -> BaselineDevice | None:
        with SessionLocal() as session:
            row = session.query(BaselineDeviceORM).filter(
                BaselineDeviceORM.ip == ip
            ).first()
            return self._to_domain(row) if row else None

    def create(self, device: BaselineDevice) -> None:
        with SessionLocal() as session:
            row = self._to_orm(device)
            session.add(row)
            session.commit()

    def update(self, ip: str, device: BaselineDevice) -> None:
        with SessionLocal() as session:
            row = session.query(BaselineDeviceORM).filter(
                BaselineDeviceORM.ip == ip
            ).first()
            if row is None:
                return
            row.ip = device.ip
            row.device_type = device.device_type.value
            row.name = device.name
            row.trusted = device.trusted
            row.can_write = device.can_write
            session.commit()

    def delete(self, ip: str) -> None:
        with SessionLocal() as session:
            row = session.query(BaselineDeviceORM).filter(
                BaselineDeviceORM.ip == ip
            ).first()
            if row is not None:
                session.delete(row)
                session.commit()

    def _to_orm(self, device: BaselineDevice) -> BaselineDeviceORM:
        return BaselineDeviceORM(
            ip=device.ip,
            device_type=device.device_type.value,
            name=device.name,
            trusted=device.trusted,
            can_write=device.can_write,
        )

    def _to_domain(self, row: BaselineDeviceORM) -> BaselineDevice:
        return BaselineDevice(
            ip=row.ip,
            device_type=DeviceType(row.device_type),
            name=row.name,
            trusted=row.trusted,
            can_write=row.can_write,
        )