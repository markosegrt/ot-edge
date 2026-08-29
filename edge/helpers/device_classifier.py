from edge.domain.enums.device_type import DeviceType


MODBUS_PORT = 502
OPCUA_PORT = 4840
S7_PORT = 102


def classify_by_ports(listening_ports: set[int]) -> DeviceType:
    if MODBUS_PORT in listening_ports:
        return DeviceType.PLC
    if S7_PORT in listening_ports:
        return DeviceType.PLC
    if OPCUA_PORT in listening_ports:
        return DeviceType.OPCUA_SERVER
    return DeviceType.UNKNOWN