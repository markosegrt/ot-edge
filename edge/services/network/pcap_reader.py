from datetime import datetime, timezone

from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP

from edge.config.settings import settings
from edge.domain.repositories.flow_repository import FlowRepository
from edge.domain.services.inventory_service import InventoryService
from edge.domain.services.event_processor import EventProcessor
from edge.domain.services.network_reader import NetworkReader
from edge.services.network.flow_builder import FlowBuilder
from edge.helpers.modbus_parser import parse_modbus


MODBUS_PORT = 502


class PcapReader(NetworkReader):
    def __init__(
        self,
        repository: FlowRepository,
        inventory: InventoryService,
        event_processor: EventProcessor,
    ):
        self.repository = repository
        self.inventory = inventory
        self.event_processor = event_processor

    def run(self) -> None:
        packets = rdpcap(settings.pcap_path)
        builder = FlowBuilder()
        write_events = []

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

            # Hvatanje Modbus 
            if int(tcp.dport) == MODBUS_PORT and bytes(tcp.payload):
                info = parse_modbus(bytes(tcp.payload))
                if info is not None and info.is_write:
                    write_events.append({
                        "src_ip": ip.src,
                        "dst_ip": ip.dst,
                        "src_port": int(tcp.sport),
                        "dst_port": int(tcp.dport),
                        "function_code": info.function_code,
                        "start_address": info.start_address,
                        "timestamp": timestamp,
                    })

        flows = builder.get_flows()

        # Prvi prolaz
        for flow in flows:
            self.repository.save(flow)
            self.inventory.observe_flow(flow)

        if flows:
            last_packet_time = max(flow.last_seen for flow in flows)
            self.inventory.check_availability(last_packet_time)

        # Drugi prolaz
        for flow in flows:
            self.event_processor.process_flow(flow)

        # Treci prolaz
        for we in write_events:
            self.event_processor.process_modbus_write(we)

        print(f"PcapReader: procitano {len(packets)} paketa, {len(flows)} tokova, {len(write_events)} upisa")