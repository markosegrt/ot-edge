"""
plant2_server.py — DRUGI PLC (ventil/pritisak)

Isti sablon kao prvi PLC: jedno stanje (Pritisak), izlozeno kroz Modbus
i OPC UA preko GENERICKIH servera. Serveri se ne diraju — mozak (Pritisak)
im opisuje sebe kroz interfejs ProcessDevice.
"""

import asyncio

from simulator.plant2 import Pritisak
from simulator.modbus_server_generic import GenericModbusServer
from simulator.opcua_server_generic import GenericOpcUaServer


TAKT_SEKUNDE = 0.1
ISPIS_NA_TAKTOVA = 20

# Drugi PLC ima svoj OPC UA namespace (razlicit od prvog)
NAMESPACE_URI = "http://otedge.local/plant2-sim"


class Plant2Server:
    def __init__(self):
        self.device = Pritisak()
        self.modbus = GenericModbusServer(self.device)
        self.opcua = GenericOpcUaServer(self.device, namespace_uri=NAMESPACE_URI)

    async def petlja_procesa(self):
        takt = 0
        while True:
            self.modbus.read_commands_from_store()
            self.device.step()
            self.modbus.write_state_to_store()

            takt += 1
            if takt % ISPIS_NA_TAKTOVA == 0:
                print(self.device.render(), flush=True)

            await asyncio.sleep(TAKT_SEKUNDE)

    async def pokreni(self):
        self.modbus.write_state_to_store()

        print("Plant2 server (PLC-2): ventil/pritisak, Modbus + OPC UA", flush=True)

        asyncio.create_task(self.modbus.run_server())
        asyncio.create_task(self.opcua.run_server())

        await asyncio.sleep(1)
        await self.petlja_procesa()


async def main():
    server = Plant2Server()
    await server.pokreni()


if __name__ == "__main__":
    asyncio.run(main())