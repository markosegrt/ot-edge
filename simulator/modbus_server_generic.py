"""
modbus_server_generic.py — GENERICKI MODBUS IZLOG

Radi sa bilo kojim mozgom koji ispunjava interfejs ProcessDevice.
Mozak kaze sta izlaze (coil_outputs, register_outputs) i kako prima
upise (apply_coils). Server je samo prenosnik — ne zna da li je pumpe
ili pritisak.
"""

import os

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncTcpServer


class GenericModbusServer:
    def __init__(self, device):
        self.device = device

        self.store = ModbusSlaveContext(
            co=ModbusSequentialDataBlock(0, [0] * 100),
            hr=ModbusSequentialDataBlock(0, [0] * 100),
        )
        self.context = ModbusServerContext(slaves=self.store, single=True)

    def write_state_to_store(self):
        """Uzmi stanje iz mozga i upisi ga u Modbus kutijice."""
        coils = self.device.coil_outputs()
        registers = self.device.register_outputs()
        for addr, val in enumerate(coils):
            self.store.setValues(1, addr, [int(val)])
        for addr, val in enumerate(registers):
            self.store.setValues(3, addr, [int(val)])

    def read_commands_from_store(self):
        """Procitaj coils iz kutijica i prosledi ih mozgu da primeni upise."""
        n = len(self.device.coil_outputs())
        if n == 0:
            return
        coils = self.store.getValues(1, 0, count=n)
        self.device.apply_coils(list(coils))

    async def run_server(self):
        port = int(os.environ.get("MODBUS_PORT", "502"))
        print(f"Modbus TCP server slusa na portu {port}", flush=True)
        await StartAsyncTcpServer(context=self.context, address=("0.0.0.0", port))