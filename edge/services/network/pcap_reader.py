# edge/services/network/pcap_reader.py
from datetime import datetime, timezone

from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP

from edge.config.settings import settings
from edge.domain.repositories.flow_repository import FlowRepository
from edge.domain.services.inventory_service import InventoryService
from edge.domain.services.network_reader import NetworkReader
from edge.services.network.flow_builder import FlowBuilder


class PcapReader(NetworkReader):
    def __init__(self, repository: FlowRepository, inventory: InventoryService):
        self.repository = repository
        self.inventory = inventory

    def run(self) -> None:
        packets = rdpcap(settings.pcap_path)
        builder = FlowBuilder()

        for packet in packets:
            if not packet.haslayer(IP) or not packet.haslayer(TCP):
                continue
            ip = packet[IP]
            tcp = packet[TCP]
            timestamp = datetime.fromtimestamp(float(packet.time), tz=timezone.utc)
            builder.add_packet(
                src_ip=ip.src,
                dst_ip=ip.dst,
                src_port=int(tcp.sport),
                dst_port=int(tcp.dport),
                size=len(packet),
                timestamp=timestamp,
            )

        flows = builder.get_flows()
        for flow in flows:
            self.repository.save(flow)
            self.inventory.observe_flow(flow)

        print(f"PcapReader: procitano {len(packets)} paketa, upisano {len(flows)} tokova")