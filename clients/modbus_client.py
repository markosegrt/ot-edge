"""
modbus_klijent.py — PARAMETRIZOVAN MODBUS KLIJENT

Jedan kod koji glumi razlicite uredjaje (HMI, SCADA, kasnije i napadaca)
u zavisnosti od PROFILA. Profil opisuje PONASANJE, kod ga izvrsava.

Zasto ovako: HMI i SCADA se razlikuju samo po ritmu i opsegu citanja.
Umesto dva skoro identicna fajla, imamo jedan + razlicite profile.
Dodavanje novog uredjaja = novi profil, ne novi fajl.

Pokretanje:
    PROFIL=hmi   MODBUS_PORT=5020 python3 modbus_klijent.py
    PROFIL=scada MODBUS_PORT=5020 python3 modbus_klijent.py
"""

import asyncio
import os
import random
from dataclasses import dataclass

from pymodbus.client import AsyncModbusTcpClient


# Iste adrese kutijica kao u serveru (ugovor o mapiranju).
COIL_PUMPA1, COIL_PUMPA2, COIL_KVAR = 0, 1, 2
REG_NIVO, REG_P1_BRZINA, REG_P2_BRZINA = 0, 1, 2


@dataclass
class Profil:
    """Opis ponasanja jednog uredjaja."""
    ime: str
    interval_citanja: float     # koliko cesto cita (sekunde)
    broj_registara: int         # koliko registara cita (opseg)
    komanduje: bool             # da li povremeno salje komande (pali/gasi)
    verovatnoca_komande: float  # sansa da posalje komandu pri svakom ciklusu


# Predefinisani profili. Ovde se dodaje novi uredjaj kad zatreba.
PROFILI = {
    # HMI: cita cesto (operater gleda uzivo), povremeno komanduje.
    "hmi": Profil(
        ime="HMI-01",
        interval_citanja=0.5,
        broj_registara=3,
        komanduje=True,
        verovatnoca_komande=0.05,   # ~5% ciklusa posalje komandu
    ),
    # SCADA: cita rede, siri opseg, ne komanduje iz sekunde u sekundu.
    "scada": Profil(
        ime="SCADA-01",
        interval_citanja=5.0,
        broj_registara=6,
        komanduje=False,
        verovatnoca_komande=0.0,
    ),
}


async def pokreni_klijent(profil: Profil, host: str, port: int):
    """Glavna petlja jednog klijenta: povezi se pa citaj (i po potrebi komanduj)."""
    client = AsyncModbusTcpClient(host, port=port)
    await client.connect()

    if not client.connected:
        print(f"[{profil.ime}] NE MOGU da se povezem na {host}:{port}")
        return

    print(f"[{profil.ime}] povezan na {host}:{port}, "
          f"citam svakih {profil.interval_citanja}s")

    ciklus = 0
    while True:
        ciklus += 1

        # --- Citanje (ovo pravi glavninu saobracaja) ---
        rr = await client.read_holding_registers(
            address=0, count=profil.broj_registara
        )
        rc = await client.read_coils(address=0, count=3)

        if not rr.isError() and not rc.isError():
            nivo = rr.registers[REG_NIVO] / 10.0
            p1 = rc.bits[COIL_PUMPA1]
            p2 = rc.bits[COIL_PUMPA2]
            # Ispisujemo povremeno da terminal ne bude pretrpan.
            if ciklus % 5 == 1:
                print(f"[{profil.ime}] Nivo={nivo:.1f}%  P1={p1}  P2={p2}")

        # --- Komanda (samo HMI, povremeno) ---
        # Ovo pravi realnu situaciju: operater ponekad upali/ugasi pumpu.
        # Kasnije ce se videti kao Modbus UPIS na mrezi - vazno za povezivanje.
        if profil.komanduje and random.random() < profil.verovatnoca_komande:
            koja = random.choice([COIL_PUMPA1, COIL_PUMPA2])
            trenutno = rc.bits[koja]
            nova = not trenutno
            await client.write_coil(koja, nova)
            pumpa = "Pumpa1" if koja == COIL_PUMPA1 else "Pumpa2"
            print(f"[{profil.ime}] KOMANDA: {pumpa} -> {'ON' if nova else 'OFF'}")

        await asyncio.sleep(profil.interval_citanja)


async def main():
    profil_ime = os.environ.get("PROFIL", "hmi").lower()
    if profil_ime not in PROFILI:
        print(f"Nepoznat profil '{profil_ime}'. Dostupni: {list(PROFILI)}")
        return

    profil = PROFILI[profil_ime]
    host = os.environ.get("MODBUS_HOST", "127.0.0.1")
    port = int(os.environ.get("MODBUS_PORT", "502"))

    await pokreni_klijent(profil, host, port)


if __name__ == "__main__":
    asyncio.run(main())
