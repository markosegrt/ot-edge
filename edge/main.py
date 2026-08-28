import asyncio

from edge.db.repositories.telemetry_repository import SqlTelemetryRepository
from edge.db.repositories.flow_repository import SqlFlowRepository
from edge.domain.services.process_reader import ProcessReader
from edge.domain.services.network_reader import NetworkReader
from edge.services.process.opcua_reader import OpcUaReader
from edge.services.network.pcap_reader import PcapReader


async def main() -> None:
    telemetry_repository = SqlTelemetryRepository()
    flow_repository = SqlFlowRepository()

    process_reader: ProcessReader = OpcUaReader(telemetry_repository)
    network_reader: NetworkReader = PcapReader(flow_repository)

    await asyncio.gather(
        process_reader.run(),
        asyncio.to_thread(network_reader.run),
    )


if __name__ == "__main__":
    asyncio.run(main())