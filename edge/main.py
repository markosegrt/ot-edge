import asyncio

from edge.config.settings import settings
from edge.db.repositories.telemetry_repository import SqlTelemetryRepository
from edge.db.repositories.flow_repository import SqlFlowRepository
from edge.db.repositories.device_repository import SqlDeviceRepository
from edge.db.repositories.security_event_repository import SqlSecurityEventRepository
from edge.domain.services.process_reader import ProcessReader
from edge.domain.services.network_reader import NetworkReader
from edge.domain.services.inventory_service import InventoryService
from edge.domain.services.event_processor import EventProcessor
from edge.domain.services.correlator import Correlator
from edge.services.process.opcua_reader import OpcUaReader
from edge.services.process.telemetry_file_reader import TelemetryFileReader
from edge.services.network.pcap_reader import PcapReader
from edge.services.network.live_reader import LiveReader
from edge.services.inventory.inventory_service import BasicInventoryService
from edge.services.normalization.normalizer import BasicNormalizer
from edge.services.correlation.correlator import BasicCorrelator
from edge.services.events.event_processor import BasicEventProcessor
from edge.services.rules.rule_engine import RuleEngine
from edge.services.rules.rule_factory import build_rules
from edge.helpers.baseline_loader import load_baseline
from edge.helpers.rules_loader import load_rules


async def main() -> None:
    telemetry_repository = SqlTelemetryRepository()
    flow_repository = SqlFlowRepository()
    device_repository = SqlDeviceRepository()
    alert_repository = SqlSecurityEventRepository()

    baseline = load_baseline(settings.baseline_path)
    inventory: InventoryService = BasicInventoryService(device_repository, baseline)

    rules = build_rules(load_rules(settings.rules_path))
    engine = RuleEngine(rules)
    normalizer = BasicNormalizer()
    correlator: Correlator = BasicCorrelator(telemetry_repository)
    event_processor: EventProcessor = BasicEventProcessor(
        normalizer, engine, correlator, device_repository, flow_repository, alert_repository, baseline
    )

    if settings.process_source == "file":
        process_reader: ProcessReader = TelemetryFileReader(telemetry_repository)
    else:
        process_reader: ProcessReader = OpcUaReader(telemetry_repository)

    if settings.network_source == "live":
        network_reader: NetworkReader = LiveReader(
            flow_repository, inventory, event_processor
        )
    else:
        network_reader: NetworkReader = PcapReader(
            flow_repository, inventory, event_processor
        )

    if settings.process_source == "file" and settings.network_source == "pcap":
        await process_reader.run()
        await asyncio.to_thread(network_reader.run)
    else:
        await asyncio.gather(
            process_reader.run(),
            asyncio.to_thread(network_reader.run),
        )


if __name__ == "__main__":
    asyncio.run(main())