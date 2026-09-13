#!/usr/bin/env bash
set -e

PCAP_PLC1="tests/pcaps/calm_plc1.pcap"
PCAP_PLC2="tests/pcaps/calm_plc2.pcap"
PCAP_SCADA="tests/pcaps/calm_scada.pcap"
TELEMETRY_OUT="tests/telemetry/calm_telemetry.jsonl"

echo "=== Snimanje MIRNOG scenarija: lanac zivi, bez napadaca ==="
echo ""

# 1. Digni lab sa lancem. HMI radi NORMALNO (komanduje pumpe/ventil).
echo "[1/7] Dizem lab (plant, plant2, scada, hmi normalan, db)..."
docker compose up -d plant plant2 scada-sim db
HMI_MODE=regulate docker compose up -d --force-recreate hmi-sim
sleep 5

# 2. Obrisi stare snimke.
echo "[2/7] Brisem stare mirne snimke..."
rm -f "$PCAP_PLC1" "$PCAP_PLC2" "$PCAP_SCADA" "$TELEMETRY_OUT"
docker compose exec plant sh -c "rm -f /tmp/cap.pcap" 2>/dev/null || true
docker compose exec plant2 sh -c "rm -f /tmp/cap.pcap" 2>/dev/null || true
docker compose exec scada-sim sh -c "rm -f /tmp/cap.pcap" 2>/dev/null || true

# 3. Pokreni tri tcpdump-a (dedup filteri, isti kao attack).
echo "[3/7] Pokrecem snimanje na 3 tacke..."
docker compose exec -d plant   tcpdump -i any -w /tmp/cap.pcap host 192.168.10.10
docker compose exec -d plant2  tcpdump -i any -w /tmp/cap.pcap host 192.168.10.11
docker compose exec -d scada-sim tcpdump -i any -w /tmp/cap.pcap host 192.168.10.20 or host 192.168.10.21

# 4. Telemetrija oba PLC-a.
echo "[4/7] Pokrecem telemetriju (oba PLC-a)..."
docker compose run --rm -d \
  --name calm-telemetry \
  -e TELEMETRY_OUTPUT="$TELEMETRY_OUT" \
  ot-edge python -m edge.tools.record_telemetry
sleep 3

# 5. Normalan rad — lanac radi, proces se menja.
echo "[5/7] Normalan rad 20s (HMI komanduje, proces zivi)..."
sleep 20

# 6. Nov LEGITIMAN uredjaj se javi (.21, drugi HMI) — izaziva RULE-001 INFO
#    "nov uredjaj". Nije napad, samo nova stanica na mrezi. Pokrece se kao
#    pravi compose servis (profil calm), bez docker-run cake sa fiksnom IP.
echo "[6/7] Nov uredjaj .21 se javlja (legitiman, kratko)..."
docker compose --profile calm up -d newdevice-sim
sleep 12
docker compose stop newdevice-sim 2>/dev/null || true
docker compose rm -f newdevice-sim 2>/dev/null || true

# 7. Zaustavi snimanja, izvuci pcap-ove.
echo "[7/7] Zaustavljam snimanje i izvlacim pcap-ove..."
docker compose exec plant     sh -c "pkill tcpdump" 2>/dev/null || true
docker compose exec plant2    sh -c "pkill tcpdump" 2>/dev/null || true
docker compose exec scada-sim sh -c "pkill tcpdump" 2>/dev/null || true
docker rm -f calm-telemetry 2>/dev/null || true
sleep 2

docker compose cp plant:/tmp/cap.pcap     "$PCAP_PLC1"
docker compose cp plant2:/tmp/cap.pcap    "$PCAP_PLC2"
docker compose cp scada-sim:/tmp/cap.pcap "$PCAP_SCADA"

echo ""
echo "=== Mirni scenario snimljen ==="
echo "  PLC1:  $(docker compose exec plant sh -c 'tcpdump -r /tmp/cap.pcap 2>/dev/null | wc -l' | tr -d '[:space:]') paketa"
echo "  PLC2:  $(docker compose exec plant2 sh -c 'tcpdump -r /tmp/cap.pcap 2>/dev/null | wc -l' | tr -d '[:space:]') paketa"
echo "  SCADA: $(docker compose exec scada-sim sh -c 'tcpdump -r /tmp/cap.pcap 2>/dev/null | wc -l' | tr -d '[:space:]') paketa"
echo "  telemetrija: $(wc -l < "$TELEMETRY_OUT" 2>/dev/null | tr -d '[:space:]') zapisa"