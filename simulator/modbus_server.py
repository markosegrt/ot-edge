"""
modbus_server.py — MREZNI IZLOG SIMULATORA (Modbus TCP, port 502)

Izlaze stanje Postrojenja na Modbus. NE otkucava proces sam —
proces otkucava zajednicka petlja u plant_server.py, da bi Modbus i OPC UA
delili ISTO stanje (jedan mozak, dva izloga), kao pravi PLC.
"""

import asyncio
import os

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncTcpServer

from simulator.plant import Postrojenje


COIL_PUMPA1 = 0
COIL_PUMPA2 = 1
COIL_KVAR = 2

REG_NIVO = 0
REG_PUMPA1_BRZINA = 1
REG_PUMPA2_BRZINA = 2


class ModbusSimulator:
    def __init__(self, postrojenje: Postrojenje):
        self.postrojenje = postrojenje

        self.store = ModbusSlaveContext(
            co=ModbusSequentialDataBlock(0, [0] * 100),
            hr=ModbusSequentialDataBlock(0, [0] * 100),
        )
        self.context = ModbusServerContext(slaves=self.store, single=True)

    def upisi_stanje_u_kutijice(self):
        s = self.postrojenje.stanje
        self.store.setValues(1, COIL_PUMPA1, [int(s.pumpa1_radi)])
        self.store.setValues(1, COIL_PUMPA2, [int(s.pumpa2_radi)])
        self.store.setValues(1, COIL_KVAR, [int(s.kvar)])
        self.store.setValues(3, REG_NIVO, [int(s.nivo * 10)])
        self.store.setValues(3, REG_PUMPA1_BRZINA, [int(s.pumpa1_brzina)])
        self.store.setValues(3, REG_PUMPA2_BRZINA, [int(s.pumpa2_brzina)])

    def procitaj_komande_iz_kutijica(self):
        p1 = self.store.getValues(1, COIL_PUMPA1, count=1)[0]
        p2 = self.store.getValues(1, COIL_PUMPA2, count=1)[0]

        if p1 and not self.postrojenje.stanje.pumpa1_radi:
            self.postrojenje.upali_pumpu1()
        elif not p1 and self.postrojenje.stanje.pumpa1_radi:
            self.postrojenje.ugasi_pumpu1()

        if p2 and not self.postrojenje.stanje.pumpa2_radi:
            self.postrojenje.upali_pumpu2()
        elif not p2 and self.postrojenje.stanje.pumpa2_radi:
            self.postrojenje.ugasi_pumpu2()

    async def pokreni_server(self):
        port = int(os.environ.get("MODBUS_PORT", "502"))
        print(f"Modbus TCP server slusa na portu {port}")
        await StartAsyncTcpServer(context=self.context, address=("0.0.0.0", port))