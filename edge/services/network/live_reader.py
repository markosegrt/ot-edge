import time
from datetime import datetime, timezone
from threading import Thread

from scapy.all import sniff
from scapy.layers.inet import IP, TCP

from edge.config.settings import settings
from edge.domain.repositories.flow_repository import FlowRepository
from edge.domain.services.inventory_service import InventoryService
from edge.domain.services.event_processor import EventProcessor
from edge.domain.services.network_reader import NetworkReader
from edge.services.network.flow_builder import FlowBuilder
from edge.helpers.modbus_parser import parse_modbus


MODBUS_PORT = 502
FLUSH_INTERVAL_SECONDS = 5


class LiveReader(NetworkReader):
    def __init__(
        self,
        repository: FlowRepository,
        inventory: InventoryService,
        event_processor: EventProcessor,
    ):
        self.repository = repository
        self.inventory = inventory
        self.event_processor = event_processor
        self.builder = FlowBuilder()
        self.write_events = []

    def run(self) -> None:
        sniff_thread = Thread(target=self._sniff, daemon=True)
        sniff_thread.start()
        print(f"LiveReader: sniffi na interfejsu, flush svakih {FLUSH_INTERVAL_SECONDS}s")

        while True:
            time.sleep(FLUSH_INTERVAL_SECONDS)
            self._flush()

    def _sniff(self) -> None:
        sniff(prn=self._handle_packet, filter="tcp port 502", store=False)

    def _handle_packet(self, packet) -> None:
        if not packet.haslayer(IP) or not packet.haslayer(TCP):
            return
        ip = packet[IP]
        tcp = packet[TCP]
        timestamp = datetime.now(timezone.utc)

        self.builder.add_packet(
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
                self.write_events.append({
                    "src_ip": ip.src,
                    "dst_ip": ip.dst,
                    "src_port": int(tcp.sport),
                    "dst_port": int(tcp.dport),
                    "function_code": info.function_code,
                    "start_address": info.start_address,
                    "timestamp": timestamp,
                })

    def _flush(self) -> None:
        flows = self.builder.get_flows()
        for flow in flows:
            self.repository.save(flow)
            self.inventory.observe_flow(flow)

        if flows:
            self.inventory.check_availability(datetime.now(timezone.utc))

        for flow in flows:
            self.event_processor.process_flow(flow)

        writes = self.write_events
        self.write_events = []
        for we in writes:
            self.event_processor.process_modbus_write(we)