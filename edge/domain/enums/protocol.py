from enum import Enum

class Protocol(str, Enum):
    MODBUS = "MODBUS"
    OPCUA = "OPCUA"
    S7 = "S7"
    OTHER = "OTHER"