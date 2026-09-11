import asyncio
import json
import os
from datetime import datetime, timezone

from asyncua import Client

from edge.config.settings import settings


PUBLISHING_INTERVAL_MS = 500
OUTPUT_PATH = os.getenv("TELEMETRY_OUTPUT", "tests/telemetry/pair_telemetry.jsonl")

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


class RecordHandler:
    """Jedan handler po PLC-u. Pise u ISTI fajl (deljeni), sa svojim device imenom."""

    def __init__(self, device_name, tag_index, output_file):
        self.device_name = device_name
        self.tag_index = tag_index
        self.output_file = output_file

    def datachange_notification(self, node, value, data):
        tag, unit = self.tag_index[node]
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device": self.device_name,
            "tag": tag,
            "value": self._to_float(value),
            "unit": unit,
            "quality": "GOOD",
        }
        self.output_file.write(json.dumps(record) + "\n")
        self.output_file.flush()

    def _to_float(self, raw):
        if isinstance(raw, bool):
            return 1.0 if raw else 0.0
        return float(raw)


async def record_plc(url, device_name, tags, output_file):
    """Snima jedan PLC. Nezavisno — reconnect ako padne."""
    while True:
        try:
            async with Client(url=url) as client:
                tag_index = {}
                for tag, path, unit in tags:
                    node = await client.nodes.root.get_child(path)
                    tag_index[node] = (tag, unit)

                handler = RecordHandler(device_name, tag_index, output_file)
                subscription = await client.create_subscription(
                    PUBLISHING_INTERVAL_MS, handler
                )
                await subscription.subscribe_data_change(list(tag_index.keys()))
                print(f"Snimam [{device_name}] preko {url}", flush=True)
                while True:
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"[{device_name}] ({url}) greska: {e} — ponovni pokusaj za 5s", flush=True)
            await asyncio.sleep(5)


async def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        tasks = [
            record_plc(settings.opcua_url, "PLC-01", PLC1_TAGS, f),
        ]
        if settings.OPCUA_HOST_2:
            tasks.append(
                record_plc(settings.opcua_url_2, "PLC-02", PLC2_TAGS, f)
            )
        print(f"Snimam telemetriju oba PLC-a u {OUTPUT_PATH}")
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())