from edge.domain.models.flow import Flow
from edge.domain.enums.protocol import Protocol
from edge.domain.repositories.flow_repository import FlowRepository
from edge.db.base import SessionLocal
from edge.db.orm.network_flow import NetworkFlowORM


class SqlFlowRepository(FlowRepository):
    def save(self, flow: Flow) -> None:
        with SessionLocal() as session:
            row = self._to_orm(flow)
            session.add(row)
            session.commit()

    def get_all(self) -> list[Flow]:
        with SessionLocal() as session:
            rows = session.query(NetworkFlowORM).all()
            return [self._to_domain(row) for row in rows]

    def _to_orm(self, flow: Flow) -> NetworkFlowORM:
        return NetworkFlowORM(
            source_ip=flow.source_ip,
            destination_ip=flow.destination_ip,
            source_port=flow.source_port,
            destination_port=flow.destination_port,
            protocol=flow.protocol.value,
            first_seen=flow.first_seen,
            last_seen=flow.last_seen,
            packet_count=flow.packet_count,
            byte_count=flow.byte_count,
        )

    def _to_domain(self, row: NetworkFlowORM) -> Flow:
        return Flow(
            source_ip=row.source_ip,
            destination_ip=row.destination_ip,
            source_port=row.source_port,
            destination_port=row.destination_port,
            protocol=Protocol(row.protocol),
            first_seen=row.first_seen,
            last_seen=row.last_seen,
            packet_count=row.packet_count,
            byte_count=row.byte_count,
        )