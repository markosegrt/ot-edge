#!/usr/bin/env bash
# demo.sh — Demonstracija OT laba: prikazuje rad svake komponente.
# Ne menja nista, samo cita logove i lepo ih prikazuje sa pauzama.

BOLD="\e[1m"
CYAN="\e[36m"
GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"
RESET="\e[0m"

pauza() {
  echo ""
  echo -e "${YELLOW}   [Enter za sledeci korak]${RESET}"
  read -r
}

clear
echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║      OT EDGE — DEMONSTRACIJA LABORATORIJE    ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "Ovaj lab simulira industrijsko postrojenje kroz vise kontejnera,"
echo "svaki sa svojom IP adresom, koji komuniciraju kao pravi uredjaji."
pauza

# --- 1. Provera da lab radi ---
echo -e "${BOLD}${CYAN}[1] KONTEJNERI (uredjaji u mrezi)${RESET}"
echo "Svaki kontejner je jedan uredjaj sa svojom IP adresom:"
echo ""
docker compose ps --format "table {{.Name}}\t{{.Status}}"
pauza

# --- 2. Mozak postrojenja ---
echo -e "${BOLD}${CYAN}[2] MOZAK POSTROJENJA (plant, .10)${RESET}"
echo -e "${GREEN}Jedno stanje procesa, otkucava se svakih 100ms."
echo -e "Pumpe pune/prazne rezervoar, nivo se menja kroz vreme:${RESET}"
echo ""
docker compose logs plant --tail 6 | grep "Nivo:"
pauza

# --- 3. HMI operater ---
echo -e "${BOLD}${CYAN}[3] HMI OPERATER (.20) — cita cesto (0.5s), komanduje${RESET}"
echo -e "${GREEN}Operaterski ekran: cita stanje uzivo, povremeno salje komandu.${RESET}"
echo ""
docker compose logs hmi-sim --tail 8
pauza

# --- 4. SCADA nadzor ---
echo -e "${BOLD}${CYAN}[4] SCADA NADZOR (.30) — cita rede (5s), samo nadzire${RESET}"
echo -e "${GREEN}Nadzorna stanica: cita rede, siri opseg, ne komanduje.${RESET}"
echo ""
docker compose logs scada-sim --tail 6
pauza

# --- 5. Modbus protokol na mrezi ---
echo -e "${BOLD}${CYAN}[5] MODBUS PROTOKOL (:502) — pravi mrezni saobracaj${RESET}"
echo -e "${GREEN}Stvarni Modbus paketi izmedju operatera i PLC-a (5 sekundi):${RESET}"
echo ""
timeout 5 docker compose exec plant tcpdump -i any -n -c 10 port 502 2>/dev/null || true
pauza

# --- 6. OPC UA protokol (procesni podaci) ---
echo -e "${BOLD}${CYAN}[6] OPC UA PROTOKOL (:4840) — procesni podaci za Edge${RESET}"
echo -e "${GREEN}Isti mozak, drugi protokol. Ovo Edge slusa kao 'procesnu istinu'."
echo -e "Trenutne vrednosti iz baze (Edge ih non-stop upisuje uzivo):${RESET}"
echo ""
docker compose exec -T db psql -U otedge -d otedge -c \
  "SELECT tag, value, timestamp FROM process_telemetry ORDER BY timestamp DESC LIMIT 6;" 2>/dev/null || \
  echo "   (Edge nije pokrenut — pokreni 'docker compose up -d ot-edge' za zive podatke)"
pauza

echo -e "${BOLD}${GREEN}"
echo "╔══════════════════════════════════════════════╗"
echo "║  Sve komponente rade. Fabrika zivi i prica.  ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"