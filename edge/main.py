import asyncio
import time
import resource

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
    correlator: Correlator = BasicCorrelator(telemetry_repository, settings.correlation_enabled)
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
        # Meri samo obradu mreze (pcap -> tokovi -> pravila -> korelacija -> baza).
        # Procesnu cev ne merimo jer je ona ucitavanje snimka, ne obrada.
        start = time.perf_counter()
        await asyncio.to_thread(network_reader.run)
        elapsed = time.perf_counter() - start
        _print_benchmark(elapsed)
    else:
        await asyncio.gather(
            process_reader.run(),
            asyncio.to_thread(network_reader.run),
        )


def _print_benchmark(elapsed_seconds: float) -> None:
    """
    Ispisuje merne pokazatelje obrade nakon jednog prolaza kroz pcap.
    ru_maxrss je vrsna rezidentna memorija procesa (na Linux-u u kilobajtima).
    ru_utime + ru_stime je ukupno CPU vreme (korisnicko + sistemsko).
    Ove vrednosti se parsiraju iz benchmark skripte za prosek preko vise prolaza.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_mem_mb = usage.ru_maxrss / 1024.0
    cpu_seconds = usage.ru_utime + usage.ru_stime

    print("=== BENCHMARK ===")
    print(f"obrada_sekundi: {elapsed_seconds:.3f}")
    print(f"vrsna_memorija_mb: {peak_mem_mb:.1f}")
    print(f"cpu_sekundi: {cpu_seconds:.3f}")


if __name__ == "__main__":
    asyncio.run(main())