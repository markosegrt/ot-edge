#!/usr/bin/env bash
set -e

# Izlazni fajlovi — tri tacke, plus zajednicka telemetrija.
PCAP_PLC1="tests/pcaps/plc1.pcap"
PCAP_PLC2="tests/pcaps/plc2.pcap"
PCAP_SCADA="tests/pcaps/scada.pcap"
TELEMETRY_OUT="tests/telemetry/pair_telemetry.jsonl"

echo "=== Snimanje punog testa: lanac + oba PLC-a + 3 napada ==="
echo ""

# 1. Digni lab sa lancem. HMI utisan (samo napadac pise u PLC direktno).
echo "[1/7] Dizem lab (plant, plant2, scada, hmi utisan, db)..."
docker compose up -d plant plant2 scada-sim db
HMI_VEROVATNOCA_KOMANDE=0 docker compose up -d --force-recreate hmi-sim
sleep 5

# 2. Obrisi stare snimke.
echo "[2/7] Brisem stare snimke..."
rm -f "$PCAP_PLC1" "$PCAP_PLC2" "$PCAP_SCADA" "$TELEMETRY_OUT"
docker compose exec plant sh -c "rm -f /tmp/cap.pcap" 2>/dev/null || true
docker compose exec plant2 sh -c "rm -f /tmp/cap.pcap" 2>/dev/null || true
docker compose exec scada-sim sh -c "rm -f /tmp/cap.pcap" 2>/dev/null || true

# 3. Pokreni tri tcpdump-a sa DEDUP filterima (bez preklapanja):
#    .10 -> sav svoj saobracaj; .11 -> sav svoj; .30 -> SAMO grana ka HMI (.20)
echo "[3/7] Pokrecem snimanje na 3 tacke (dedup filteri)..."
docker compose exec -d plant   tcpdump -i any -w /tmp/cap.pcap host 192.168.10.10
docker compose exec -d plant2  tcpdump -i any -w /tmp/cap.pcap host 192.168.10.11
docker compose exec -d scada-sim tcpdump -i any -w /tmp/cap.pcap host 192.168.10.20

# 4. Pokreni telemetriju oba PLC-a (zaseban kontejner).
echo "[4/7] Pokrecem telemetriju (oba PLC-a)..."
docker compose run --rm -d \
  -e TELEMETRY_OUTPUT="$TELEMETRY_OUT" \
  ot-edge python -m edge.tools.record_telemetry
sleep 3

# 5. Normalan rad par sekundi (za "normalu" u snimku).
echo "[5/7] Normalan rad 15s..."
sleep 15

# 6. Pusti tri napada redom.
echo "[6/7] Napad 1/3: port scan (.99 -> .10)..."
docker compose run --rm -e ATTACK=scan rogue-sim
sleep 5

echo "        Napad 2/3: sabotaza ventila (.99 -> .11, pritisak raste)..."
docker compose run --rm -e ATTACK=pressure -e TARGET_HOST_2=192.168.10.11 rogue-sim
sleep 5

echo "        Napad 3/3: flood (.99 -> .10)..."
docker compose run --rm -e ATTACK=flood rogue-sim
sleep 5

# 7. Zaustavi snimanja, izvuci tri pcap-a.
echo "[7/7] Zaustavljam snimanje i izvlacim pcap-ove..."
docker compose exec plant     sh -c "pkill tcpdump" 2>/dev/null || true
docker compose exec plant2    sh -c "pkill tcpdump" 2>/dev/null || true
docker compose exec scada-sim sh -c "pkill tcpdump" 2>/dev/null || true
docker compose exec ot-edge   sh -c "pkill -f record_telemetry" 2>/dev/null || true
sleep 2

docker compose cp plant:/tmp/cap.pcap     "$PCAP_PLC1"
docker compose cp plant2:/tmp/cap.pcap    "$PCAP_PLC2"
docker compose cp scada-sim:/tmp/cap.pcap "$PCAP_SCADA"

echo ""
echo "=== Gotovo ==="
echo "  PLC1 pcap:  $(docker compose exec plant sh -c 'tcpdump -r /tmp/cap.pcap 2>/dev/null | wc -l' | tr -d '[:space:]') paketa"
echo "  PLC2 pcap:  $(docker compose exec plant2 sh -c 'tcpdump -r /tmp/cap.pcap 2>/dev/null | wc -l' | tr -d '[:space:]') paketa"
echo "  SCADA pcap: $(docker compose exec scada-sim sh -c 'tcpdump -r /tmp/cap.pcap 2>/dev/null | wc -l' | tr -d '[:space:]') paketa"
echo "  telemetrija: $(wc -l < "$TELEMETRY_OUT" 2>/dev/null | tr -d '[:space:]') zapisa"
echo ""
echo "Za pustanje kroz Edge, postavi u docker-compose ot-edge:"
echo "  PCAP_PATH: $PCAP_PLC1,$PCAP_PLC2,$PCAP_SCADA"
echo "  RUN_MODE: measurement"