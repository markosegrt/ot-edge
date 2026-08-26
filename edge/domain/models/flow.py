from dataclasses import dataclass
from datetime import datetime

from edge.domain.enums.protocol import Protocol


@dataclass
class Flow:
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: Protocol
    first_seen: datetime
    last_seen: datetime
    packet_count: int
    byte_count: int