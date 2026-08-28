from datetime import datetime, timezone

from edge.domain.enums.protocol import Protocol
from edge.domain.models.flow import Flow


MODBUS_PORT = 502
OPCUA_PORT = 4840


class FlowBuilder:
    def __init__(self):
        self._flows: dict[tuple, Flow] = {}

    def add_packet(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int, size: int, timestamp: datetime) -> None:
        key = (src_ip, dst_ip, src_port, dst_port)
        flow = self._flows.get(key)
        if flow is None:
            self._flows[key] = Flow(
                source_ip=src_ip,
                destination_ip=dst_ip,
                source_port=src_port,
                destination_port=dst_port,
                protocol=self._detect_protocol(src_port, dst_port),
                first_seen=timestamp,
                last_seen=timestamp,
                packet_count=1,
                byte_count=size,
            )
        else:
            flow.last_seen = timestamp
            flow.packet_count += 1
            flow.byte_count += size

    def get_flows(self) -> list[Flow]:
        return list(self._flows.values())

    def _detect_protocol(self, src_port: int, dst_port: int) -> Protocol:
        if MODBUS_PORT in (src_port, dst_port):
            return Protocol.MODBUS
        if OPCUA_PORT in (src_port, dst_port):
            return Protocol.OPCUA
        return Protocol.OTHER