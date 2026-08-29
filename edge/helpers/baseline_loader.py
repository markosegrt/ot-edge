import yaml

from edge.domain.enums.device_type import DeviceType
from edge.domain.models.baseline_device import BaselineDevice


def load_baseline(path: str) -> dict[str, BaselineDevice]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    result = {}
    for entry in data.get("devices", []):
        device = BaselineDevice(
            ip=entry["ip"],
            device_type=DeviceType(entry["type"]),
            name=entry["name"],
            trusted=entry.get("trusted", True),
        )
        result[device.ip] = device
    return result