"""
modbus_klijent.py — PARAMETRIZOVAN MODBUS KLIJENT

Jedan kod koji glumi razlicite uredjaje (HMI, SCADA, kasnije i napadaca)
u zavisnosti od PROFILA. Profil opisuje PONASANJE, kod ga izvrsava.

VAZNO (lanac HMI -> SCADA -> PLC): HMI se povezuje na SCADA-u (.30), NE na PLC.
Cita objedinjenu procesnu sliku (process image) oba PLC-a sa SCADA-e, i sve
komande salje SCADA-i, koja ih prosledi pravom PLC-u.

Komande su CILJNE (postavi na ON/OFF), ne toggle — nema ping-ponga.

HMI ima dva rezima komandovanja (HMI_MODE):
  - regulate: pametno drzi proces u normali (nivo ~50, pritisak ~30).
              Koristi se za MIRAN scenario — proces zivi ali je stabilan.
  - random:   nasumicno pali/gasi (staro ponasanje). Za attack scenario,
              gde napadac ionako pravi glavni haos.

Pokretanje:
    PROFIL=hmi MODBUS_HOST=192.168.10.30 HMI_MODE=regulate python3 -m clients.modbus_client
"""

import asyncio
import os
import random
from dataclasses import dataclass

from pymodbus.client import AsyncModbusTcpClient


# Adrese u procesnoj slici (ugovor sa scada_proxy.py).
COIL_PUMP1, COIL_PUMP2, COIL_FAULT1 = 0, 1, 2
COIL_VALVE, COIL_FAULT2 = 10, 11
REG_LEVEL, REG_P1SPEED, REG_P2SPEED = 0, 1, 2
REG_PRESSURE = 10

# Ciljne vrednosti za regulate rezim (drzimo proces oko ovoga).
LEVEL_LOW, LEVEL_HIGH = 25.0, 75.0        
PRESSURE_LOW, PRESSURE_HIGH = 10.0, 75.0  


@dataclass
class Profil:
    """Opis ponasanja jednog uredjaja."""
    ime: str
    interval_citanja: float
    komanduje: bool
    verovatnoca_komande: float


PROFILI = {
    "hmi": Profil(
        ime="HMI-01",
        interval_citanja=0.5,
        komanduje=True,
        verovatnoca_komande=float(os.environ.get("HMI_VEROVATNOCA_KOMANDE", "0.05")),
    ),
    "scada": Profil(
        ime="SCADA-01",
        interval_citanja=5.0,
        komanduje=False,
        verovatnoca_komande=0.0,
    ),
}


def regulate_command(level, pressure, p1, p2, valve):
    """
    Pametna regulacija: vrati (coil_adresa, ciljna_vrednost, opis) da vrati
    proces ka normali, ili None ako je sve u redu. Operater odrzava proces.
    """
    # Nivo prenizak -> upali pumpu1 (puni)
    if level < LEVEL_LOW and not p1:
        return (COIL_PUMP1, 1, "Pump1 -> ON (nivo nizak)")
    # Nivo previsok -> ugasi pumpu1 (staje punjenje)
    if level > LEVEL_HIGH and p1:
        return (COIL_PUMP1, 0, "Pump1 -> OFF (nivo visok)")
    # Pritisak previsok -> otvori ventil (ispusta)
    if pressure > PRESSURE_HIGH and not valve:
        return (COIL_VALVE, 1, "Valve -> OPEN (pritisak visok)")
    # Pritisak prenizak -> zatvori ventil (drzi)
    if pressure < PRESSURE_LOW and valve:
        return (COIL_VALVE, 0, "Valve -> CLOSED (pritisak nizak)")
    # Sve u normali — nista ne diramo.
    return None


def random_command(p1, p2, valve):
    """Staro nasumicno ponasanje: preokreni jedan slucajan aktuator."""
    izbor = random.choice(["pump1", "pump2", "valve"])
    if izbor == "pump1":
        return (COIL_PUMP1, 0 if p1 else 1, f"Pump1 -> {'OFF' if p1 else 'ON'}")
    elif izbor == "pump2":
        return (COIL_PUMP2, 0 if p2 else 1, f"Pump2 -> {'OFF' if p2 else 'ON'}")
    else:
        return (COIL_VALVE, 0 if valve else 1, f"Valve -> {'CLOSED' if valve else 'OPEN'}")


async def pokreni_klijent(profil: Profil, host: str, port: int, hmi_mode: str):
    """Glavna petlja: povezi se pa citaj (i po potrebi komanduj)."""
    client = AsyncModbusTcpClient(host, port=port)
    await client.connect()

    if not client.connected:
        print(f"[{profil.ime}] NE MOGU da se povezem na {host}:{port}")
        return

    print(f"[{profil.ime}] povezan na {host}:{port}, "
          f"citam svakih {profil.interval_citanja}s, rezim={hmi_mode}")

    ciklus = 0
    while True:
        ciklus += 1

        rr = await client.read_holding_registers(address=0, count=11)
        rc = await client.read_coils(address=0, count=12)

        stanje = None
        if not rr.isError() and not rc.isError():
            level = rr.registers[REG_LEVEL] / 10.0
            pressure = rr.registers[REG_PRESSURE] / 10.0
            p1 = rc.bits[COIL_PUMP1]
            p2 = rc.bits[COIL_PUMP2]
            valve = rc.bits[COIL_VALVE]
            stanje = (level, pressure, p1, p2, valve)
            if ciklus % 5 == 1:
                print(f"[{profil.ime}] Level={level:.1f}%  P1={p1}  P2={p2}  "
                      f"Pressure={pressure:.1f}bar  Valve={'OPEN' if valve else 'CLOSED'}")

        # --- Komanda ---
        if profil.komanduje and stanje is not None:
            level, pressure, p1, p2, valve = stanje
            komanda = None

            if hmi_mode == "regulate":
                # Pametno: gledaj stanje i vracaj ka normali (bez verovatnoce,
                # ali samo kad stvarno treba korekcija).
                komanda = regulate_command(level, pressure, p1, p2, valve)
            else:
                # Nasumicno, sa verovatnocom (staro ponasanje).
                if random.random() < profil.verovatnoca_komande:
                    komanda = random_command(p1, p2, valve)

            if komanda is not None:
                coil, cilj, opis = komanda
                await client.write_coil(coil, bool(cilj))
                print(f"[{profil.ime}] KOMANDA: {opis}")

        await asyncio.sleep(profil.interval_citanja)


async def main():
    profil_ime = os.environ.get("PROFIL", "hmi").lower()
    if profil_ime not in PROFILI:
        print(f"Nepoznat profil '{profil_ime}'. Dostupni: {list(PROFILI)}")
        return

    profil = PROFILI[profil_ime]
    host = os.environ.get("MODBUS_HOST", "127.0.0.1")
    port = int(os.environ.get("MODBUS_PORT", "502"))
    hmi_mode = os.environ.get("HMI_MODE", "random").lower()

    await pokreni_klijent(profil, host, port, hmi_mode)


if __name__ == "__main__":
    asyncio.run(main())