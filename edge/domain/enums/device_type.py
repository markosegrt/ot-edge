from enum import Enum

class DeviceType(str, Enum):
    PLC = "PLC"
    HMI = "HMI"
    SCADA = "SCADA"
    OPCUA_SERVER = "OPCUA_SERVER"
    UNKNOWN = "UNKNOWN"