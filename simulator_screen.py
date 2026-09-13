#!/usr/bin/env python3
"""
simulator_screen.py — KONZOLNI PANEL ZA PRIKAZ SIMULATORA I NAPADACA

Sluzi za demonstraciju: bira se komponenta iz menija, prikaze se kratko
objasnjenje sta ona radi, pa zivi log te komponente (vrednosti se menjaju
u realnom vremenu). Za napadaca — pokrece se napad i prati se sta radi.

Ne dira kod ni bazu — samo cita logove i (za napadaca) pokrece postojeci
rogue-sim. Bezbedno za demonstraciju.

Pokretanje:  python3 simulator_screen.py
Izlaz iz zivog loga:  Ctrl+C (vraca u meni).
"""

import subprocess
import sys


# Boje za citljiviji ispis
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BLUE = "\033[34m"
RESET = "\033[0m"


def run(cmd):
    """Pokreni komandu, prikazi izlaz uzivo."""
    subprocess.run(cmd, shell=True)


def ensure_lab():
    """Digni lab ako ne radi (simulatori + baza)."""
    print(f"{CYAN}Proveravam da lab radi...{RESET}")
    run("docker compose up -d plant plant2 hmi-sim scada-sim db")
    print(f"{GREEN}Lab spreman.{RESET}\n")


def show_live_log(service, opis):
    """Prikazi objasnjenje pa zivi log jedne komponente."""
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(opis)
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{YELLOW}Zivi log — vrednosti se menjaju u realnom vremenu.{RESET}")
    print(f"{YELLOW}Pritisni Ctrl+C da se vratis u meni.{RESET}\n")
    try:
        run(f"docker compose logs -f --tail=15 {service}")
    except KeyboardInterrupt:
        pass
    print(f"\n{GREEN}Vracam u meni...{RESET}")


def plc1():
    opis = (
        f"{BOLD}PLC1 — POSTROJENJE (pumpe / nivo rezervoara){RESET}\n\n"
        "Prvi kontroler. Upravlja sa dve pumpe i rezervoarom:\n"
        f"  {GREEN}Pumpa1{RESET} puni rezervoar, {GREEN}Pumpa2{RESET} ga prazni.\n"
        "  Nivo raste/pada u zavisnosti od pumpi. Kad predje granice\n"
        "  (prepun/prazan) javlja se KVAR.\n\n"
        "  Izlaze stanje kroz Modbus (:502) i OPC UA (:4840).\n"
        "  U logu vidis: Nivo %, koja pumpa radi, i kvar ako ga ima."
    )
    show_live_log("plant", opis)


def plc2():
    opis = (
        f"{BOLD}PLC2 — REGULACIJA PRITISKA (ventil / pritisak){RESET}\n\n"
        "Drugi kontroler, druga fizika. Upravlja ventilom i pritiskom:\n"
        f"  {GREEN}Ventil OTVOREN{RESET} -> pritisak pada (ispusta se).\n"
        f"  {GREEN}Ventil ZATVOREN{RESET} -> pritisak raste (nema kud).\n"
        "  Ako pritisak predje opasnu granicu -> KVAR.\n\n"
        "  Ovo je meta napada 'sabotaza ventila': napadac zatvori ventil,\n"
        "  pritisak skoci do opasnog. U logu vidis: Pritisak bar, stanje ventila."
    )
    show_live_log("plant2", opis)


def hmi():
    opis = (
        f"{BOLD}HMI — OPERATERSKA STANICA (.20){RESET}\n\n"
        "Operaterski panel. NE prica direktno sa PLC-om, nego sa SCADA-om\n"
        "(lanac HMI -> SCADA -> PLC, Purdue model).\n\n"
        f"  Cita objedinjenu procesnu sliku sa SCADA-e (nivo, pritisak, ventil).\n"
        f"  Povremeno {GREEN}komanduje{RESET} (pali/gasi pumpe, otvara/zatvara ventil)\n"
        "  da odrzi proces u normali.\n\n"
        "  U logu vidis: sta HMI cita (Level, Pressure, Valve) i koje komande salje."
    )
    show_live_log("hmi-sim", opis)


def scada():
    opis = (
        f"{BOLD}SCADA — NADZORNA STANICA (.30){RESET}\n\n"
        "Sredina lanca. Jedina prica direktno sa oba PLC-a:\n"
        f"  {GREEN}Cita{RESET} stanje sa PLC1 i PLC2 (dva Modbus klijenta).\n"
        f"  {GREEN}Objedinjuje{RESET} ga u procesnu sliku koju HMI cita.\n"
        f"  {GREEN}Prosledjuje{RESET} komande sa HMI-ja pravom PLC-u.\n\n"
        "  Jedini je OVLASCEN da pise u PLC (can_write). Zato napad koji\n"
        "  pise direktno u PLC (zaobilazi SCADA-u) sistem hvata kao neovlascen.\n\n"
        "  U logu vidis: komande koje SCADA prosledjuje PLC-ovima."
    )
    show_live_log("scada-sim", opis)


def napadac():
    print(f"\n{BOLD}{RED}{'='*60}{RESET}")
    print(f"{BOLD}NAPADAC — ROGUE UREDJAJ (.99){RESET}\n")
    print("Nepoznat uredjaj koji NIJE u listi poznatih. Izvodi vise napada:")
    print(f"  {RED}scan{RESET}     — skeniranje portova (izvidjanje)")
    print(f"  {RED}pressure{RESET} — sabotaza ventila PLC2 (pritisak skace)")
    print(f"  {RED}flood{RESET}    — poplava Modbus zahteva (DoS)")
    print(f"  {RED}rampage{RESET}  — svi napadi zaredom (pun napad)")
    print(f"{BOLD}{RED}{'='*60}{RESET}\n")

    print("Koji napad da pokrenem?")
    print("  1. scan (port scan)")
    print("  2. pressure (sabotaza ventila)")
    print("  3. flood (DoS)")
    print("  4. rampage (pun napad — sve zaredom)")
    print("  0. nazad")
    izbor = input(f"{YELLOW}Izbor: {RESET}").strip()

    mapa = {"1": "scan", "2": "pressure", "3": "flood", "4": "rampage"}
    if izbor not in mapa:
        return

    attack = mapa[izbor]
    print(f"\n{RED}Pokrecem napad: {attack}{RESET}\n")
    # rogue-sim ima profil 'attack' — pokrecemo ga sa izabranim napadom.
    run(f"docker compose run --rm -e ATTACK={attack} "
        f"-e TARGET_HOST_2=192.168.10.11 rogue-sim")
    print(f"\n{GREEN}Napad zavrsen. Enter za povratak u meni.{RESET}")
    input()


def stanje_procesa():
    """Prikazi trenutno stanje iz baze (poslednje procesne vrednosti)."""
    print(f"\n{BOLD}{CYAN}TRENUTNO STANJE PROCESA (iz baze){RESET}\n")
    run(
        "docker compose exec -T db psql -U otedge -d otedge -c "
        "\"SELECT device_name, tag, value FROM process_telemetry "
        "WHERE (device_name, tag, timestamp) IN "
        "(SELECT device_name, tag, MAX(timestamp) FROM process_telemetry "
        "GROUP BY device_name, tag) ORDER BY device_name, tag;\""
    )
    print(f"\n{GREEN}Enter za povratak.{RESET}")
    input()


def meni():
    while True:
        print(f"\n{BOLD}{CYAN}")
        print("╔══════════════════════════════════════════════╗")
        print("║      OT EDGE — PANEL SIMULATORA I NAPADACA   ║")
        print("╚══════════════════════════════════════════════╝")
        print(RESET)
        print(f"  {GREEN}1{RESET}. PLC1 — pumpe / nivo (zivi log)")
        print(f"  {GREEN}2{RESET}. PLC2 — ventil / pritisak (zivi log)")
        print(f"  {GREEN}3{RESET}. HMI — operaterska stanica (zivi log)")
        print(f"  {GREEN}4{RESET}. SCADA — nadzorna stanica (zivi log)")
        print(f"  {RED}5{RESET}. NAPADAC — pokreni napad")
        print(f"  {BLUE}6{RESET}. Trenutno stanje procesa (iz baze)")
        print(f"  {YELLOW}0{RESET}. Izlaz")
        izbor = input(f"\n{YELLOW}Izbor: {RESET}").strip()

        if izbor == "1":
            plc1()
        elif izbor == "2":
            plc2()
        elif izbor == "3":
            hmi()
        elif izbor == "4":
            scada()
        elif izbor == "5":
            napadac()
        elif izbor == "6":
            stanje_procesa()
        elif izbor == "0":
            print(f"{GREEN}Izlaz.{RESET}")
            break
        else:
            print(f"{RED}Nepoznata opcija.{RESET}")


if __name__ == "__main__":
    ensure_lab()
    try:
        meni()
    except KeyboardInterrupt:
        print(f"\n{GREEN}Prekid. Izlaz.{RESET}")
        sys.exit(0)