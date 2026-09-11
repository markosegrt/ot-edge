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
from edge.db.repositories.baseline_repository import SqlBaselineRepository
from edge.helpers.rules_loader import load_rules


def build_components():
    telemetry_repository = SqlTelemetryRepository()
    flow_repository = SqlFlowRepository()
    device_repository = SqlDeviceRepository()
    alert_repository = SqlSecurityEventRepository()

    baseline_repository = SqlBaselineRepository()
    baseline = {d.ip: d for d in baseline_repository.get_all()}
    inventory: InventoryService = BasicInventoryService(device_repository, baseline)

    rules = build_rules(load_rules(settings.rules_path), telemetry_repository)
    engine = RuleEngine(rules)
    normalizer = BasicNormalizer()
    correlator: Correlator = BasicCorrelator(telemetry_repository, settings.correlation_enabled)
    event_processor: EventProcessor = BasicEventProcessor(
        normalizer, engine, correlator, device_repository, flow_repository, alert_repository, baseline
    )
    return telemetry_repository, flow_repository, device_repository, inventory, event_processor


async def run_measurement_once() -> None:
    """Merni mod: jedan prolaz kroz snimak (telemetrija pa mreza), pa izlaz.
    Koristi se za merenja iz eksperimentalnog dela (pusti isti pcap, izmeri)."""
    telemetry_repository, flow_repository, device_repository, inventory, event_processor = build_components()
    process_reader: ProcessReader = TelemetryFileReader(telemetry_repository)
    network_reader: NetworkReader = PcapReader(flow_repository, inventory, event_processor)

    await process_reader.run()
    start = time.perf_counter()
    await asyncio.to_thread(network_reader.run)
    elapsed = time.perf_counter() - start
    _print_benchmark(elapsed)


async def run_live() -> None:
    """Non-stop mod: Edge stalno radi.
    - proces: OPC UA subscription cita PLC uzivo (ne izlazi)
    - mreza: periodicno cita pcap koji tcpdump puni u pozadini
    Oba zajedno preko asyncio.gather, tako da Edge non-stop nadzire."""
    telemetry_repository, flow_repository, device_repository, inventory, event_processor = build_components()

    process_reader: ProcessReader = OpcUaReader(telemetry_repository)

    tasks = [process_reader.run()]

    # Mrezni deo ukljucujemo samo ako je zadat (deo B). Za sad, u koraku A,
    # ostavljamo ga iskljucenim dok ne dodamo periodicnu obradu pcap-a.
    if settings.network_enabled:
        network_reader: NetworkReader = PcapReader(flow_repository, inventory, event_processor)
        tasks.append(asyncio.to_thread(_network_loop, network_reader))

    print("Edge: non-stop mod pokrenut (proces uzivo preko OPC UA)")
    await asyncio.gather(*tasks)


def _network_loop(network_reader) -> None:
    """Deo B: periodicno obradjuje pcap koji tcpdump puni. Dodajemo u sledecem koraku."""
    import time as _time
    while True:
        network_reader.run()
        _time.sleep(settings.network_interval_seconds)


async def main() -> None:
    if settings.run_mode == "measurement":
        await run_measurement_once()
    else:
        await run_live()


def _print_benchmark(elapsed_seconds: float) -> None:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_mem_mb = usage.ru_maxrss / 1024.0
    cpu_seconds = usage.ru_utime + usage.ru_stime
    print("=== BENCHMARK ===")
    print(f"obrada_sekundi: {elapsed_seconds:.3f}")
    print(f"vrsna_memorija_mb: {peak_mem_mb:.1f}")
    print(f"cpu_sekundi: {cpu_seconds:.3f}")


if __name__ == "__main__":
    asyncio.run(main())