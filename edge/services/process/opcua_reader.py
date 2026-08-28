import asyncio
from datetime import datetime, timezone
from edge.domain.services.process_reader import ProcessReader
from asyncua import Client, Node

from edge.config.settings import settings
from edge.domain.enums.quality import Quality
from edge.domain.models.telemetry import Telemetry
from edge.domain.repositories.telemetry_repository import TelemetryRepository


DEVICE_NAME = "PLC-01"
PUBLISHING_INTERVAL_MS = 500

TAGS = [
    ("Pumpa1.Radi", ["0:Objects", "2:Postrojenje", "2:Pumpa1", "2:Radi"], None),
    ("Pumpa1.Brzina", ["0:Objects", "2:Postrojenje", "2:Pumpa1", "2:Brzina"], "Hz"),
    ("Pumpa2.Radi", ["0:Objects", "2:Postrojenje", "2:Pumpa2", "2:Radi"], None),
    ("Pumpa2.Brzina", ["0:Objects", "2:Postrojenje", "2:Pumpa2", "2:Brzina"], "Hz"),
    ("Rezervoar.Nivo", ["0:Objects", "2:Postrojenje", "2:Rezervoar", "2:Nivo"], "%"),
    ("Rezervoar.Kvar", ["0:Objects", "2:Postrojenje", "2:Rezervoar", "2:Kvar"], None),
]


class TelemetryHandler:
    def __init__(self, repository: TelemetryRepository, tag_index: dict[Node, tuple[str, str | None]]):
        self.repository = repository
        self.tag_index = tag_index

    def datachange_notification(self, node: Node, value, data) -> None:
        tag, unit = self.tag_index[node]
        telemetry = Telemetry(
            timestamp=datetime.now(timezone.utc),
            device=DEVICE_NAME,
            tag=tag,
            value=self._to_float(value),
            unit=unit,
            quality=Quality.GOOD,
        )
        self.repository.save(telemetry)

    def _to_float(self, raw) -> float:
        if isinstance(raw, bool):
            return 1.0 if raw else 0.0
        return float(raw)


class OpcUaReader(ProcessReader):
    def __init__(self, repository: TelemetryRepository):
        self.repository = repository

    async def run(self) -> None:
        async with Client(url=settings.opcua_url) as client:
            tag_index = await self._resolve_nodes(client)
            handler = TelemetryHandler(self.repository, tag_index)

            subscription = await client.create_subscription(PUBLISHING_INTERVAL_MS, handler)
            await subscription.subscribe_data_change(list(tag_index.keys()))

            print(f"OPC UA reader: pretplacen na {len(tag_index)} vrednosti preko {settings.opcua_url}")
            await self._keep_alive()

    async def _resolve_nodes(self, client: Client) -> dict[Node, tuple[str, str | None]]:
        tag_index = {}
        for tag, path, unit in TAGS:
            node = await client.nodes.root.get_child(path)
            tag_index[node] = (tag, unit)
        return tag_index

    async def _keep_alive(self) -> None:
        while True:
            await asyncio.sleep(1)