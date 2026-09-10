"""
modbus_klijent.py — PARAMETRIZOVAN MODBUS KLIJENT

Jedan kod koji glumi razlicite uredjaje (HMI, SCADA, kasnije i napadaca)
u zavisnosti od PROFILA. Profil opisuje PONASANJE, kod ga izvrsava.

VAZNO (lanac HMI -> SCADA -> PLC): HMI se povezuje na SCADA-u (.30), NE na PLC.
Cita objedinjenu procesnu sliku (process image) oba PLC-a sa SCADA-e, i sve
komande salje SCADA-i, koja ih prosledi pravom PLC-u.

Komande su CILJNE (postavi na ON/OFF), ne toggle — nema ping-ponga.

Pokretanje:
    PROFIL=hmi   MODBUS_HOST=192.168.10.30 python3 -m clients.modbus_client
"""

import asyncio
import os
import random
from dataclasses import dataclass

from pymodbus.client import AsyncModbusTcpClient


# Adrese u procesnoj slici (ugovor sa scada_proxy.py).
# PLC1 na 0-2, PLC2 na 10+ (isti raspored kao u SCADA process image).
COIL_PUMP1, COIL_PUMP2, COIL_FAULT1 = 0, 1, 2
COIL_VALVE, COIL_FAULT2 = 10, 11
REG_LEVEL, REG_P1SPEED, REG_P2SPEED = 0, 1, 2
REG_PRESSURE = 10


@dataclass
class Profil:
    """Opis ponasanja jednog uredjaja."""
    ime: str
    interval_citanja: float     # koliko cesto cita (sekunde)
    komanduje: bool             # da li povremeno salje komande
    verovatnoca_komande: float  # sansa da posalje komandu pri svakom ciklusu


PROFILI = {
    # HMI: cita cesto (operater gleda uzivo), povremeno komanduje.
    "hmi": Profil(
        ime="HMI-01",
        interval_citanja=0.5,
        komanduje=True,
        verovatnoca_komande=float(os.environ.get("HMI_VEROVATNOCA_KOMANDE", "0.05")),
    ),
    # SCADA profil ostaje za kompatibilnost, ali SCADA se sad pokrece preko
    # scada_proxy.py — ne preko ovog klijenta.
    "scada": Profil(
        ime="SCADA-01",
        interval_citanja=5.0,
        komanduje=False,
        verovatnoca_komande=0.0,
    ),
}


async def pokreni_klijent(profil: Profil, host: str, port: int):
    """Glavna petlja: povezi se pa citaj (i po potrebi komanduj) ciljnim stanjem."""
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

        # --- Citanje procesne slike (oba PLC-a) ---
        # Citamo dovoljno da pokrijemo i PLC2 (do registra/coila 11).
        rr = await client.read_holding_registers(address=0, count=11)
        rc = await client.read_coils(address=0, count=12)

        pumpe_stanje = None
        if not rr.isError() and not rc.isError():
            level = rr.registers[REG_LEVEL] / 10.0
            pressure = rr.registers[REG_PRESSURE] / 10.0
            p1 = rc.bits[COIL_PUMP1]
            p2 = rc.bits[COIL_PUMP2]
            valve = rc.bits[COIL_VALVE]
            pumpe_stanje = (p1, p2, valve)
            if ciklus % 5 == 1:
                print(f"[{profil.ime}] Level={level:.1f}%  P1={p1}  P2={p2}  "
                      f"Pressure={pressure:.1f}bar  Valve={'OPEN' if valve else 'CLOSED'}")

        # --- Komanda (samo HMI, povremeno) ---
        # Operater postavi CILJNO stanje nekog aktuatora (pumpa1/pumpa2/ventil)
        # na suprotno od trenutnog. Upis ide SCADA-i, koja prosledi PLC-u.
        if profil.komanduje and pumpe_stanje is not None \
                and random.random() < profil.verovatnoca_komande:
            p1, p2, valve = pumpe_stanje
            # Biramo koji aktuator diramo: pumpa1, pumpa2 ili ventil (PLC2).
            izbor = random.choice(["pump1", "pump2", "valve"])

            if izbor == "pump1":
                cilj = 0 if p1 else 1
                await client.write_coil(COIL_PUMP1, bool(cilj))
                print(f"[{profil.ime}] KOMANDA: Pump1 -> {'ON' if cilj else 'OFF'}")
            elif izbor == "pump2":
                cilj = 0 if p2 else 1
                await client.write_coil(COIL_PUMP2, bool(cilj))
                print(f"[{profil.ime}] KOMANDA: Pump2 -> {'ON' if cilj else 'OFF'}")
            else:  # valve
                cilj = 0 if valve else 1
                await client.write_coil(COIL_VALVE, bool(cilj))
                print(f"[{profil.ime}] KOMANDA: Valve -> {'OPEN' if cilj else 'CLOSED'}")

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