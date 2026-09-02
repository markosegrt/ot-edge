from pydantic import BaseModel

from edge.db.repositories.flow_repository import SqlFlowRepository
from edge.db.repositories.device_repository import SqlDeviceRepository


class NetworkNode(BaseModel):
    ip: str
    device_type: str
    status: str


class NetworkLink(BaseModel):
    source: str
    target: str
    protocol: str
    packet_count: int


class NetworkResponse(BaseModel):
    nodes: list[NetworkNode]
    links: list[NetworkLink]


class NetworkController:
    def __init__(self):
        self.flow_repository = SqlFlowRepository()
        self.device_repository = SqlDeviceRepository()

    def get_network(self) -> NetworkResponse:
        devices = self.device_repository.get_all()
        device_by_ip = {d.ip: d for d in devices}

        flows = self.flow_repository.get_all()
        links_map: dict[tuple[str, str, str], int] = {}
        node_ips: set[str] = set()

        for flow in flows:
            key = (flow.source_ip, flow.destination_ip, flow.protocol.value)
            links_map[key] = links_map.get(key, 0) + flow.packet_count
            node_ips.add(flow.source_ip)
            node_ips.add(flow.destination_ip)

        nodes = []
        for ip in sorted(node_ips):
            device = device_by_ip.get(ip)
            nodes.append(
                NetworkNode(
                    ip=ip,
                    device_type=device.device_type.value if device else "UNKNOWN",
                    status=device.status.value if device else "NEW",
                )
            )

        links = [
            NetworkLink(source=src, target=dst, protocol=proto, packet_count=count)
            for (src, dst, proto), count in links_map.items()
        ]

        return NetworkResponse(nodes=nodes, links=links)