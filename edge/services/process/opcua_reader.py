import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

from asyncua import Client, Node

from edge.config.settings import settings
from edge.domain.enums.quality import Quality
from edge.domain.models.telemetry import Telemetry
from edge.domain.repositories.telemetry_repository import TelemetryRepository
from edge.domain.services.process_reader import ProcessReader


PUBLISHING_INTERVAL_MS = 500


PLC1_TAGS = [
    ("Pumpa1.Radi", ["0:Objects", "2:Postrojenje", "2:Pumpa1", "2:Radi"], None),
    ("Pumpa1.Brzina", ["0:Objects", "2:Postrojenje", "2:Pumpa1", "2:Brzina"], "Hz"),
    ("Pumpa2.Radi", ["0:Objects", "2:Postrojenje", "2:Pumpa2", "2:Radi"], None),
    ("Pumpa2.Brzina", ["0:Objects", "2:Postrojenje", "2:Pumpa2", "2:Brzina"], "Hz"),
    ("Rezervoar.Nivo", ["0:Objects", "2:Postrojenje", "2:Rezervoar", "2:Nivo"], "%"),
    ("Rezervoar.Kvar", ["0:Objects", "2:Postrojenje", "2:Rezervoar", "2:Kvar"], None),
]

PLC2_TAGS = [
    ("Ventil.Otvoren", ["0:Objects", "2:Postrojenje", "2:Ventil", "2:Otvoren"], None),
    ("Cev.Pritisak", ["0:Objects", "2:Postrojenje", "2:Cev", "2:Pritisak"], "bar"),
    ("Cev.Kvar", ["0:Objects", "2:Postrojenje", "2:Cev", "2:Kvar"], None),
]


def _host_from_url(url: str) -> str:
    """Izvuce IP/host iz opc.tcp URL-a (za device_ip u telemetriji)."""
    return urlparse(url).hostname or ""


class TelemetryHandler:
    def __init__(
        self,
        repository: TelemetryRepository,
        device_name: str,
        device_ip: str,
        tag_index: dict[Node, tuple[str, str | None]],
    ):
        self.repository = repository
        self.device_name = device_name
        self.device_ip = device_ip
        self.tag_index = tag_index

    def datachange_notification(self, node: Node, value, data) -> None:
        tag, unit = self.tag_index[node]
        telemetry = Telemetry(
            timestamp=datetime.now(timezone.utc),
            device=self.device_name,
            device_ip=self.device_ip,
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


class SinglePlcReader:
    def __init__(
        self,
        repository: TelemetryRepository,
        url: str,
        device_name: str,
        device_ip: str,
        tags: list,
    ):
        self.repository = repository
        self.url = url
        self.device_name = device_name
        self.device_ip = device_ip
        self.tags = tags

    async def run(self) -> None:
        while True:
            try:
                async with Client(url=self.url) as client:
                    tag_index = await self._resolve_nodes(client)
                    handler = TelemetryHandler(
                        self.repository, self.device_name, self.device_ip, tag_index
                    )

                    subscription = await client.create_subscription(
                        PUBLISHING_INTERVAL_MS, handler
                    )
                    await subscription.subscribe_data_change(list(tag_index.keys()))

                    print(
                        f"OPC UA reader [{self.device_name} / {self.device_ip}]: "
                        f"pretplacen na {len(tag_index)} vrednosti preko {self.url}",
                        flush=True,
                    )
                    await self._keep_alive()
            except Exception as e:
                print(
                    f"OPC UA reader [{self.device_name}] ({self.url}) greska: {e} "
                    f"— ponovni pokusaj za 5s",
                    flush=True,
                )
                await asyncio.sleep(5)

    async def _resolve_nodes(self, client: Client) -> dict[Node, tuple[str, str | None]]:
        tag_index = {}
        for tag, path, unit in self.tags:
            node = await client.nodes.root.get_child(path)
            tag_index[node] = (tag, unit)
        return tag_index

    async def _keep_alive(self) -> None:
        while True:
            await asyncio.sleep(1)


class OpcUaReader(ProcessReader):
    def __init__(self, repository: TelemetryRepository):
        self.repository = repository

        self.readers = [
            SinglePlcReader(
                repository,
                settings.opcua_url,
                "PLC-01",
                _host_from_url(settings.opcua_url),
                PLC1_TAGS,
            ),
        ]

        if settings.OPCUA_HOST_2:
            self.readers.append(
                SinglePlcReader(
                    repository,
                    settings.opcua_url_2,
                    "PLC-02",
                    _host_from_url(settings.opcua_url_2),
                    PLC2_TAGS,
                )
            )

    async def run(self) -> None:
        await asyncio.gather(*(r.run() for r in self.readers))