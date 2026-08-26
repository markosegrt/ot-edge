from enum import Enum

class EventType(str, Enum):
    NETWORK = "NETWORK"
    PROCESS = "PROCESS"