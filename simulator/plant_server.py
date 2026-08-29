"""
plant_server.py — JEDINSTVENI SIMULATOR POSTROJENJA

Jedan proces koji glumi pravi PLC: jedno stanje (Postrojenje), izlozeno
kroz DVA protokola istovremeno — Modbus TCP (:502) i OPC UA (:4840).
Oba izloga dele ISTO stanje, pa mreza i proces uvek opisuju istu istinu.
Ovo je preduslov za povezivanje mreznih i procesnih dogadjaja.
"""

import asyncio

from simulator.plant import Postrojenje
from simulator.modbus_server import ModbusSimulator
from simulator.opcua_server import OpcUaSimulator


TAKT_SEKUNDE = 0.1


class PlantServer:
    def __init__(self):
        self.postrojenje = Postrojenje()
        self.modbus = ModbusSimulator(self.postrojenje)
        self.opcua = OpcUaSimulator(self.postrojenje)

    async def petlja_procesa(self):
        """Jedina petlja koja otkucava proces. Oba izloga citaju ovo stanje."""
        while True:
            self.modbus.procitaj_komande_iz_kutijica()
            self.postrojenje.korak()
            self.modbus.upisi_stanje_u_kutijice()
            await asyncio.sleep(TAKT_SEKUNDE)

    async def pokreni(self):
        self.postrojenje.upali_pumpu1()
        self.postrojenje.upali_pumpu2()
        self.modbus.upisi_stanje_u_kutijice()

        print("Plant server: jedan mozak, Modbus :502 + OPC UA :4840")

        
        asyncio.create_task(self.modbus.pokreni_server())
        asyncio.create_task(self.opcua.pokreni_server())

        await asyncio.sleep(1)
        await self.petlja_procesa()


async def main():
    server = PlantServer()
    await server.pokreni()


if __name__ == "__main__":
    asyncio.run(main())