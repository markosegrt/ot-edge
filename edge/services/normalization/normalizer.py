from edge.domain.enums.event_type import EventType
from edge.domain.enums.severity import Severity
from edge.domain.models.event import Event
from edge.domain.models.flow import Flow
from edge.domain.services.normalizer import Normalizer


class BasicNormalizer(Normalizer):
    def from_flow(self, flow: Flow) -> Event:
        return Event(
            timestamp=flow.last_seen,
            event_type=EventType.NETWORK,
            severity=Severity.INFO,
            source=flow.source_ip,
            destination=flow.destination_ip,
            device=flow.destination_ip,
            protocol=flow.protocol,
            extra={
                "source_port": flow.source_port,
                "destination_port": flow.destination_port,
                "packet_count": flow.packet_count,
                "byte_count": flow.byte_count,
            },
        )