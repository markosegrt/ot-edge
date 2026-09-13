#!/usr/bin/env bash
set -e

PCAPS="tests/pcaps/attack_plc1.pcap,tests/pcaps/attack_plc2.pcap,tests/pcaps/attack_scada.pcap"
TELEMETRY="tests/telemetry/attack_telemetry.jsonl"

echo "╔══════════════════════════════════════════════╗"
echo "║   TEST 2 — NAPAD SCENARIO (bogat napad)      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1. Digni bazu i API ako ne rade.
echo "[1/5] Dizem bazu i API..."
docker compose up -d db api
sleep 3

# 2. Zaustavi live Edge i ocisti zaostale run-kontejnere.
echo "[2/5] Zaustavljam live Edge (ako radi)..."
docker compose stop ot-edge 2>/dev/null || true
docker rm -f $(docker ps -aq --filter "name=ot-edge-ot-edge-run") 2>/dev/null || true

# 3. Ocisti bazu — baseline i pravila ostaju.
echo "[3/5] Cistim bazu (baseline i pravila ostaju)..."
docker compose exec -T db psql -U otedge -d otedge \
  -c "TRUNCATE network_flows, security_events, process_telemetry, devices, correlations, incidents RESTART IDENTITY CASCADE;" > /dev/null

# 4. Ucitaj NAPAD scenario kroz Edge (measurement).
echo "[4/5] Ucitavam napad scenario (obrada snimka)..."
docker compose run --rm \
  -e PCAP_PATH="$PCAPS" \
  -e TELEMETRY_PATH="$TELEMETRY" \
  -e RUN_MODE=measurement \
  -e CORRELATION_ENABLED=true \
  ot-edge

# 5. Prikazi rezime — alarmi sa count-om i korelacije.
echo ""
echo "[5/5] Detektovano u napad scenariju:"
echo ""
echo "--- ALARMI (sa brojem ponavljanja) ---"
docker compose exec -T db psql -U otedge -d otedge -c "
  SELECT rule_id, severity, occurrence_count AS count, source, destination
  FROM security_events
  ORDER BY rule_id, id;
"
echo "--- KORELACIJE (pre/posle) ---"
docker compose exec -T db psql -U otedge -d otedge -c "
  SELECT event_id, pattern, base_severity AS pre, final_severity AS posle
  FROM correlations;
"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  NAPAD SCENARIO UCITAN — otvori dashboard:   ║"
echo "║  http://localhost:5173                       ║"
echo "╚══════════════════════════════════════════════╝"