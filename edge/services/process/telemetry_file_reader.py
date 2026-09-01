import json
from datetime import datetime

from edge.config.settings import settings
from edge.domain.enums.quality import Quality
from edge.domain.models.telemetry import Telemetry
from edge.domain.repositories.telemetry_repository import TelemetryRepository
from edge.domain.services.process_reader import ProcessReader


class TelemetryFileReader(ProcessReader):
    def __init__(self, repository: TelemetryRepository):
        self.repository = repository

    async def run(self) -> None:
        path = settings.telemetry_path
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                telemetry = Telemetry(
                    timestamp=datetime.fromisoformat(record["timestamp"]),
                    device=record["device"],
                    tag=record["tag"],
                    value=float(record["value"]),
                    unit=record["unit"],
                    quality=Quality(record["quality"]),
                )
                self.repository.save(telemetry)
                count += 1

        print(f"TelemetryFileReader: upisano {count} zapisa telemetrije iz snimka")