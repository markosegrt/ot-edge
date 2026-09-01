# edge/tools/record_telemetry.py
import asyncio
import json
import os
from datetime import datetime, timezone

from asyncua import Client

from edge.config.settings import settings


DEVICE_NAME = "PLC-01"
PUBLISHING_INTERVAL_MS = 500
OUTPUT_PATH = os.getenv("TELEMETRY_OUTPUT", "tests/telemetry/pair_telemetry.jsonl")

TAGS = [
    ("Pumpa1.Radi", ["0:Objects", "2:Postrojenje", "2:Pumpa1", "2:Radi"], None),
    ("Pumpa1.Brzina", ["0:Objects", "2:Postrojenje", "2:Pumpa1", "2:Brzina"], "Hz"),
    ("Pumpa2.Radi", ["0:Objects", "2:Postrojenje", "2:Pumpa2", "2:Radi"], None),
    ("Pumpa2.Brzina", ["0:Objects", "2:Postrojenje", "2:Pumpa2", "2:Brzina"], "Hz"),
    ("Rezervoar.Nivo", ["0:Objects", "2:Postrojenje", "2:Rezervoar", "2:Nivo"], "%"),
    ("Rezervoar.Kvar", ["0:Objects", "2:Postrojenje", "2:Rezervoar", "2:Kvar"], None),
]


class RecordHandler:
    def __init__(self, tag_index, output_file):
        self.tag_index = tag_index
        self.output_file = output_file

    def datachange_notification(self, node, value, data):
        tag, unit = self.tag_index[node]
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device": DEVICE_NAME,
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


async def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    async with Client(url=settings.opcua_url) as client:
        tag_index = {}
        for tag, path, unit in TAGS:
            node = await client.nodes.root.get_child(path)
            tag_index[node] = (tag, unit)

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            handler = RecordHandler(tag_index, f)
            subscription = await client.create_subscription(PUBLISHING_INTERVAL_MS, handler)
            await subscription.subscribe_data_change(list(tag_index.keys()))
            print(f"Snimam telemetriju u {OUTPUT_PATH}")
            while True:
                await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())