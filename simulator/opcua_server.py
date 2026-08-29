"""
opcua_server.py — PROCESNI IZLOG SIMULATORA (OPC UA, port 4840)

Izlaze stanje Postrojenja preko OPC UA. NE otkucava proces sam —
proces otkucava zajednicka petlja u plant_server.py, da bi Modbus i OPC UA
delili ISTO stanje (jedan mozak, dva izloga), kao pravi PLC.
"""

import asyncio
import os

from asyncua import Server

from simulator.plant import Postrojenje


NAMESPACE_URI = "http://otedge.local/plant-sim"


class OpcUaSimulator:
    def __init__(self, postrojenje: Postrojenje):
        self.postrojenje = postrojenje
        self.server = Server()
        self.cvorovi = {}

    async def podesi(self):
        await self.server.init()

        port = int(os.environ.get("OPCUA_PORT", "4840"))
        self.server.set_endpoint(f"opc.tcp://0.0.0.0:{port}/otedge/")
        self.server.set_server_name("OT Edge Plant Simulator")

        idx = await self.server.register_namespace(NAMESPACE_URI)

        objekti = self.server.nodes.objects
        postrojenje_obj = await objekti.add_object(idx, "Postrojenje")

        pumpa1 = await postrojenje_obj.add_object(idx, "Pumpa1")
        self.cvorovi["p1_radi"] = await pumpa1.add_variable(idx, "Radi", False)
        self.cvorovi["p1_brzina"] = await pumpa1.add_variable(idx, "Brzina", 0.0)

        pumpa2 = await postrojenje_obj.add_object(idx, "Pumpa2")
        self.cvorovi["p2_radi"] = await pumpa2.add_variable(idx, "Radi", False)
        self.cvorovi["p2_brzina"] = await pumpa2.add_variable(idx, "Brzina", 0.0)

        rezervoar = await postrojenje_obj.add_object(idx, "Rezervoar")
        self.cvorovi["nivo"] = await rezervoar.add_variable(idx, "Nivo", 0.0)
        self.cvorovi["kvar"] = await rezervoar.add_variable(idx, "Kvar", False)

        for cvor in self.cvorovi.values():
            await cvor.set_writable(False)

        print(f"OPC UA server podesen na opc.tcp://0.0.0.0:{port}/otedge/")

    async def osvezi_vrednosti(self):
        s = self.postrojenje.stanje
        await self.cvorovi["p1_radi"].write_value(s.pumpa1_radi)
        await self.cvorovi["p1_brzina"].write_value(float(s.pumpa1_brzina))
        await self.cvorovi["p2_radi"].write_value(s.pumpa2_radi)
        await self.cvorovi["p2_brzina"].write_value(float(s.pumpa2_brzina))
        await self.cvorovi["nivo"].write_value(float(s.nivo))
        await self.cvorovi["kvar"].write_value(s.kvar)

    async def pokreni_server(self):
        await self.podesi()
        async with self.server:
            print("OPC UA server: radi.")
            while True:
                await self.osvezi_vrednosti()
                await asyncio.sleep(0.1)