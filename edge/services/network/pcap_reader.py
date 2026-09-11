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

    def _pcap_paths(self) -> list[str]:
        """
        Vraca listu pcap fajlova. settings.pcap_path moze biti:
          - jedan fajl:   "tests/pcaps/pair.pcap"
          - vise fajlova: "tests/pcaps/plc1.pcap,tests/pcaps/plc2.pcap,..."
        Filteri pri snimanju garantuju da se paketi NE preklapaju izmedju
        fajlova, pa ih samo ucitavamo sve u isti FlowBuilder.
        """
        raw = settings.pcap_path
        return [p.strip() for p in raw.split(",") if p.strip()]

    def run(self) -> None:
        paths = self._pcap_paths()
        edge_ip = settings.edge_ip

        builder = FlowBuilder()
        write_events = []
        total_packets = 0

        for path in paths:
            packets = rdpcap(path)
            total_packets += len(packets)

            for packet in packets:
                if not packet.haslayer(IP) or not packet.haslayer(TCP):
                    continue
                ip = packet[IP]
                tcp = packet[TCP]

                # Edge (sniffer) je posmatrac — njegov OPC UA saobracaj ka PLC-u
                # nije deo osmotrene mreze. Preskacemo ga na ulazu da ne pravi
                # lazne uredjaje/alarme (RULE-002/003 na .50).
                if ip.src == edge_ip or ip.dst == edge_ip:
                    continue

                timestamp = datetime.fromtimestamp(float(packet.time), tz=timezone.utc)

                builder.add_packet(
                    src_ip=ip.src,
                    dst_ip=ip.dst,
                    src_port=int(tcp.sport),
                    dst_port=int(tcp.dport),
                    size=len(packet),
                    timestamp=timestamp,
                )

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

        if total_packets == 0:
            print("PcapReader: prazni pcap fajlovi")
            return

        flows = builder.get_flows()

        for flow in flows:
            self.repository.save(flow)
            self.inventory.observe_flow(flow)

        if flows:
            unavailable = self.inventory.check_availability(datetime.now(timezone.utc))
            for device in unavailable:
                self.event_processor.process_unavailable_device(device)

        for flow in flows:
            self.event_processor.process_flow(flow)

        for we in write_events:
            self.event_processor.process_modbus_write(we)

        print(
            f"PcapReader: {len(paths)} fajl(ova), procitano {total_packets} paketa, "
            f"{len(flows)} tokova, {len(write_events)} upisa"
        )