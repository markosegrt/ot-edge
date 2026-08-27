import asyncio

from edge.db.repositories.telemetry_repository import SqlTelemetryRepository
from edge.services.process.opcua_reader import OpcUaReader


async def main() -> None:
    telemetry_repository = SqlTelemetryRepository()
    opcua_reader = OpcUaReader(telemetry_repository)

    await opcua_reader.run()


if __name__ == "__main__":
    asyncio.run(main())