from edge.domain.enums.event_type import EventType
from edge.domain.enums.severity import Severity
from edge.domain.models.event import Event
from edge.domain.models.flow import Flow
from edge.domain.services.normalizer import Normalizer
from edge.domain.enums.protocol import Protocol

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

    def from_modbus_write(
        self, src_ip, dst_ip, src_port, dst_port,
        function_code, start_address, timestamp,
    ) -> Event:
        return Event(
            timestamp=timestamp,
            event_type=EventType.NETWORK,
            severity=Severity.INFO,
            source=src_ip,
            destination=dst_ip,
            device=dst_ip,
            protocol=Protocol.MODBUS,
            extra={
                "modbus_write": True,
                "function_code": function_code,
                "start_address": start_address,
                "source_port": src_port,
                "destination_port": dst_port,
            },
        )