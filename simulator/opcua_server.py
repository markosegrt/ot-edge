"""
opcua_server.py — PROCESNI IZLOG SIMULATORA (OPC UA, port 4840)

Zadatak: uzeti isto stanje iz plant.py i izloziti ga preko OPC UA,
tako da ga tvoj Edge cita kao "istinu o procesu".

Razlika u odnosu na Modbus:
  Modbus = numerisane kutijice sa golim brojevima (ti pamtis sta je sta).
  OPC UA = imenovane vrednosti sa tipom i jedinicom, u stablu:

    Postrojenje
      Pumpa1.Radi (bool), Pumpa1.Brzina (float)
      Pumpa2.Radi (bool), Pumpa2.Brzina (float)
      Rezervoar.Nivo (float), Rezervoar.Kvar (bool)

Server radi DVE stvari paralelno (asyncio):
  1) otkucava postrojenje na 100ms
  2) osvezava OPC UA vrednosti da klijent (Edge) cita azurno stanje
"""

import asyncio
import os

from asyncua import Server, ua

from simulator.plant import Postrojenje


# Namespace = "imenski prostor", jedinstvena oznaka naseg modela u OPC UA.
# Klijent ce ga koristiti da pronadje nase vrednosti.
NAMESPACE_URI = "http://otedge.local/plant-sim"


class OpcUaSimulator:
    def __init__(self, postrojenje: Postrojenje):
        # VAZNO: prima postojece Postrojenje spolja, ne pravi svoje.
        # Zasto: kasnije cemo hteti da Modbus i OPC UA dele ISTO postrojenje
        # (jedan izvor istine, dva izloga). Za sada svaki moze imati svoje.
        self.postrojenje = postrojenje
        self.server = Server()
        self.cvorovi = {}   # ovde cuvamo reference na OPC UA vrednosti

    async def podesi(self):
        """Napravi OPC UA server, stablo cvorova i registruj namespace."""
        await self.server.init()

        port = int(os.environ.get("OPCUA_PORT", "4840"))
        self.server.set_endpoint(f"opc.tcp://0.0.0.0:{port}/otedge/")
        self.server.set_server_name("OT Edge Plant Simulator")

        # Registruj nas namespace i zapamti njegov indeks (idx).
        idx = await self.server.register_namespace(NAMESPACE_URI)

        # Napravi glavni objekat "Postrojenje" pod Objects cvorom.
        objekti = self.server.nodes.objects
        postrojenje_obj = await objekti.add_object(idx, "Postrojenje")

        # Napravi pod-objekte i njihove promenljive.
        # add_variable(idx, ime, pocetna_vrednost) pravi citljivu vrednost.
        pumpa1 = await postrojenje_obj.add_object(idx, "Pumpa1")
        self.cvorovi["p1_radi"] = await pumpa1.add_variable(idx, "Radi", False)
        self.cvorovi["p1_brzina"] = await pumpa1.add_variable(idx, "Brzina", 0.0)

        pumpa2 = await postrojenje_obj.add_object(idx, "Pumpa2")
        self.cvorovi["p2_radi"] = await pumpa2.add_variable(idx, "Radi", False)
        self.cvorovi["p2_brzina"] = await pumpa2.add_variable(idx, "Brzina", 0.0)

        rezervoar = await postrojenje_obj.add_object(idx, "Rezervoar")
        self.cvorovi["nivo"] = await rezervoar.add_variable(idx, "Nivo", 0.0)
        self.cvorovi["kvar"] = await rezervoar.add_variable(idx, "Kvar", False)

        # Ove vrednosti server sam upisuje (writable=False za klijenta).
        # Klijent (Edge) ih samo CITA - tako i treba, Edge ne upravlja procesom.
        for cvor in self.cvorovi.values():
            await cvor.set_writable(False)

        print(f"OPC UA server podesen na opc.tcp://0.0.0.0:{port}/otedge/")

    async def _osvezi_vrednosti(self):
        """Prepisi trenutno stanje postrojenja u OPC UA cvorove."""
        s = self.postrojenje.stanje
        # write_value sa eksplicitnim tipom da OPC UA zna sta je sta.
        await self.cvorovi["p1_radi"].write_value(s.pumpa1_radi)
        await self.cvorovi["p1_brzina"].write_value(float(s.pumpa1_brzina))
        await self.cvorovi["p2_radi"].write_value(s.pumpa2_radi)
        await self.cvorovi["p2_brzina"].write_value(float(s.pumpa2_brzina))
        await self.cvorovi["nivo"].write_value(float(s.nivo))
        await self.cvorovi["kvar"].write_value(s.kvar)

    async def petlja(self):
        """Otkucaj postrojenje i osvezi OPC UA vrednosti, na 100ms."""
        while True:
            self.postrojenje.korak()
            await self._osvezi_vrednosti()
            await asyncio.sleep(0.1)

    async def pokreni(self):
        await self.podesi()
        # Postavi pocetno stanje: obe pumpe rade (normalan rad).
        self.postrojenje.upali_pumpu1()
        self.postrojenje.upali_pumpu2()

        async with self.server:
            print("OPC UA simulator: server radi, otkucavam proces.")
            await self.petlja()


async def main():
    postrojenje = Postrojenje()
    sim = OpcUaSimulator(postrojenje)
    await sim.pokreni()


if __name__ == "__main__":
    asyncio.run(main())
