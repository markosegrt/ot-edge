"""
plant_server.py — PRVI PLC (pumpe/nivo)

Jedan proces koji glumi PLC: jedno stanje (Postrojenje), izlozeno kroz
Modbus TCP (:502) i OPC UA (:4840) preko GENERICKIH servera.
Serveri ne znaju da li je mozak pumpe ili pritisak — mozak im opisuje sebe
kroz interfejs ProcessDevice.
"""

import asyncio

from simulator.plant import Postrojenje
from simulator.modbus_server_generic import GenericModbusServer
from simulator.opcua_server_generic import GenericOpcUaServer


TAKT_SEKUNDE = 0.1
ISPIS_NA_TAKTOVA = 20


class PlantServer:
    def __init__(self):
        self.device = Postrojenje()
        self.modbus = GenericModbusServer(self.device)
        self.opcua = GenericOpcUaServer(self.device)

    async def petlja_procesa(self):
        """Jedina petlja koja otkucava proces. Oba izloga citaju ovo stanje."""
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
        # Startno stanje: obe pumpe rade (normalan rad, nivo lebdi oko 50%)
        self.device.upali_pumpu1()
        self.device.upali_pumpu2()
        self.modbus.write_state_to_store()

        print("Plant server: jedan mozak, Modbus :502 + OPC UA :4840", flush=True)

        asyncio.create_task(self.modbus.run_server())
        asyncio.create_task(self.opcua.run_server())

        await asyncio.sleep(1)
        await self.petlja_procesa()


async def main():
    server = PlantServer()
    await server.pokreni()


if __name__ == "__main__":
    asyncio.run(main())