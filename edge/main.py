# edge/main.py
import asyncio

from edge.config.settings import settings
from edge.db.repositories.telemetry_repository import SqlTelemetryRepository
from edge.db.repositories.flow_repository import SqlFlowRepository
from edge.db.repositories.device_repository import SqlDeviceRepository
from edge.domain.services.process_reader import ProcessReader
from edge.domain.services.network_reader import NetworkReader
from edge.domain.services.inventory_service import InventoryService
from edge.services.process.opcua_reader import OpcUaReader
from edge.services.network.pcap_reader import PcapReader
from edge.services.inventory.inventory_service import BasicInventoryService
from edge.helpers.baseline_loader import load_baseline


async def main() -> None:
    telemetry_repository = SqlTelemetryRepository()
    flow_repository = SqlFlowRepository()
    device_repository = SqlDeviceRepository()

    baseline = load_baseline(settings.baseline_path)
    inventory: InventoryService = BasicInventoryService(device_repository, baseline)

    process_reader: ProcessReader = OpcUaReader(telemetry_repository)
    network_reader: NetworkReader = PcapReader(flow_repository, inventory)

    await asyncio.gather(
        process_reader.run(),
        asyncio.to_thread(network_reader.run),
    )


if __name__ == "__main__":
    asyncio.run(main())