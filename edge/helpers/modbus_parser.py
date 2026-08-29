from dataclasses import dataclass


WRITE_FUNCTION_CODES = {5, 6, 15, 16}
READ_FUNCTION_CODES = {1, 2, 3, 4}

MBAP_HEADER_SIZE = 7


@dataclass
class ModbusInfo:
    function_code: int
    is_write: bool
    start_address: int | None


def parse_modbus(payload: bytes) -> ModbusInfo | None:
    if len(payload) < MBAP_HEADER_SIZE + 1:
        return None

    function_code = payload[MBAP_HEADER_SIZE]
    is_write = function_code in WRITE_FUNCTION_CODES

    start_address = None
    if len(payload) >= MBAP_HEADER_SIZE + 3:
        start_address = int.from_bytes(payload[MBAP_HEADER_SIZE + 1:MBAP_HEADER_SIZE + 3], "big")

    return ModbusInfo(
        function_code=function_code,
        is_write=is_write,
        start_address=start_address,
    )