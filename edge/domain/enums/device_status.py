from enum import Enum

class DeviceStatus(str, Enum):
    NEW = "NEW"
    KNOWN = "KNOWN"
    UNAVAILABLE = "UNAVAILABLE"