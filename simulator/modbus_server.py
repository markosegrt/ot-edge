"""
modbus_server.py — MREZNI IZLOG SIMULATORA (Modbus TCP, port 502)

Zadatak: uzeti stanje iz plant.py i izloziti ga na mrezu preko Modbus-a,
tako da HMI/SCADA (i kasnije napadac) mogu da ga citaju i menjaju.

Modbus ne zna za "pumpe" i "nivoe" - zna samo za numerisane kutijice:
  COILS             - drze DA/NE (1 bit)
  HOLDING REGISTERS - drze ceo broj (16 bita)

UGOVOR O MAPIRANJU (svi ucesnici moraju znati isto):
  COIL 0   -> Pumpa1 radi (0/1)
  COIL 1   -> Pumpa2 radi (0/1)
  COIL 2   -> Kvar (0/1)
  REGISTAR 0 -> Nivo rezervoara (% x10, npr 548 = 54.8%)
  REGISTAR 1 -> Pumpa1 brzina (Hz)
  REGISTAR 2 -> Pumpa2 brzina (Hz)

Server radi DVE stvari paralelno (preko asyncio):
  1) otkucava postrojenje na 100ms i osvezava kutijice
  2) slusa mrezu i odgovara na Modbus citanja/upise
"""

import asyncio

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncTcpServer

from simulator.plant import Postrojenje


# ---- Adrese kutijica (ugovor iz gornjeg opisa, na jednom mestu) ----
COIL_PUMPA1 = 0
COIL_PUMPA2 = 1
COIL_KVAR = 2

REG_NIVO = 0
REG_PUMPA1_BRZINA = 1
REG_PUMPA2_BRZINA = 2


class ModbusSimulator:
    """
    Spaja Postrojenje (mozak) sa Modbus skladistem (kutijice).
    'context' je Modbus skladiste koje pymodbus izlaze na mrezu.
    """

    def __init__(self):
        self.postrojenje = Postrojenje()

        # Napravi prazno skladiste: 100 coil-ova i 100 registara, sve na 0.
        # (100 je vise nego dovoljno; ostavljamo mesta za buducа prosirenja.)
        self.store = ModbusSlaveContext(
            co=ModbusSequentialDataBlock(0, [0] * 100),   # coils
            hr=ModbusSequentialDataBlock(0, [0] * 100),   # holding registers
        )
        self.context = ModbusServerContext(slaves=self.store, single=True)

    def _upisi_stanje_u_kutijice(self):
        """
        Uzmi trenutno stanje postrojenja i upisi ga u Modbus kutijice,
        da bi ga onaj ko cita sa mreze video azurnog.
        """
        s = self.postrojenje.stanje

        # Coils: DA/NE vrednosti. Modbus ih vidi kao listu bool/int.
        # 'setValues(1, adresa, [...])' - 1 je Modbus kod za coils.
        self.store.setValues(1, COIL_PUMPA1, [int(s.pumpa1_radi)])
        self.store.setValues(1, COIL_PUMPA2, [int(s.pumpa2_radi)])
        self.store.setValues(1, COIL_KVAR, [int(s.kvar)])

        # Registri: celi brojevi. Nivo x10 da sacuvamo jednu decimalu.
        # 'setValues(3, adresa, [...])' - 3 je Modbus kod za holding registre.
        self.store.setValues(3, REG_NIVO, [int(s.nivo * 10)])
        self.store.setValues(3, REG_PUMPA1_BRZINA, [int(s.pumpa1_brzina)])
        self.store.setValues(3, REG_PUMPA2_BRZINA, [int(s.pumpa2_brzina)])

    def _procitaj_komande_iz_kutijica(self):
        """
        Obrnut smer: ako je neko sa mreze upisao u coil (npr. upalio pumpu),
        procitaj to i primeni na postrojenje.
        Ovo je ono sto kasnije napadac zloupotrebljava (upis u registre).
        """
        # getValues(1, adresa, count) - procitaj coils
        p1 = self.store.getValues(1, COIL_PUMPA1, count=1)[0]
        p2 = self.store.getValues(1, COIL_PUMPA2, count=1)[0]

        # Primeni na postrojenje samo ako se stanje razlikuje
        if p1 and not self.postrojenje.stanje.pumpa1_radi:
            self.postrojenje.upali_pumpu1()
        elif not p1 and self.postrojenje.stanje.pumpa1_radi:
            self.postrojenje.ugasi_pumpu1()

        if p2 and not self.postrojenje.stanje.pumpa2_radi:
            self.postrojenje.upali_pumpu2()
        elif not p2 and self.postrojenje.stanje.pumpa2_radi:
            self.postrojenje.ugasi_pumpu2()

    async def petlja_procesa(self):
        """
        Beskonacna petlja koja otkucava postrojenje na 100ms.
        Redosled: procitaj komande sa mreze -> otkucaj -> upisi novo stanje.
        """
        while True:
            self._procitaj_komande_iz_kutijica()
            self.postrojenje.korak()
            self._upisi_stanje_u_kutijice()
            await asyncio.sleep(0.1)   # 100ms takt


async def main():
    sim = ModbusSimulator()

    # Postavi neko smisleno pocetno stanje: obe pumpe rade (normalan rad).
    sim.postrojenje.upali_pumpu1()
    sim.postrojenje.upali_pumpu2()
    sim._upisi_stanje_u_kutijice()

    print("Modbus simulator: startujem takt procesa i TCP server na :502")

    # Pokreni petlju procesa u pozadini (ne blokira server).
    asyncio.create_task(sim.petlja_procesa())

    # Pokreni Modbus TCP server. '0.0.0.0' = slusaj na svim adresama
    # (bitno za Docker kasnije). Ovo blokira i drzi program zivim.
    import os
    port = int(os.environ.get("MODBUS_PORT", "502"))
    print(f"Modbus TCP server slusa na portu {port}")
    await StartAsyncTcpServer(context=sim.context, address=("0.0.0.0", port))


if __name__ == "__main__":
    asyncio.run(main())
