from edge.domain.models.telemetry import Telemetry
from edge.domain.enums.quality import Quality
from edge.domain.repositories.telemetry_repository import TelemetryRepository
from edge.db.base import SessionLocal
from edge.db.orm.process_telemetry import ProcessTelemetryORM
from datetime import datetime

class SqlTelemetryRepository(TelemetryRepository):
    def save(self, telemetry: Telemetry) -> None:
        with SessionLocal() as session:
            row = self._to_orm(telemetry)
            session.add(row)
            session.commit()

    def get_all(self) -> list[Telemetry]:
        with SessionLocal() as session:
            rows = session.query(ProcessTelemetryORM).all()
            return [self._to_domain(row) for row in rows]

    def _to_orm(self, telemetry: Telemetry) -> ProcessTelemetryORM:
        return ProcessTelemetryORM(
            timestamp=telemetry.timestamp,
            device_name=telemetry.device,
            tag=telemetry.tag,
            value=telemetry.value,
            unit=telemetry.unit,
            quality=telemetry.quality.value,
        )

    def _to_domain(self, row: ProcessTelemetryORM) -> Telemetry:
        return Telemetry(
            timestamp=row.timestamp,
            device=row.device_name,
            tag=row.tag,
            value=row.value,
            unit=row.unit,
            quality=Quality(row.quality),
        )

    def get_between(self, start: datetime, end: datetime) -> list[Telemetry]:
        with SessionLocal() as session:
            rows = (
                session.query(ProcessTelemetryORM)
                .filter(ProcessTelemetryORM.timestamp >= start)
                .filter(ProcessTelemetryORM.timestamp <= end)
                .all()
            )
            return [self._to_domain(row) for row in rows]