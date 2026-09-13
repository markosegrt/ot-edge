#!/usr/bin/env bash
set -e

PCAPS="tests/pcaps/calm_plc1.pcap,tests/pcaps/calm_plc2.pcap,tests/pcaps/calm_scada.pcap"
TELEMETRY="tests/telemetry/calm_telemetry.jsonl"

echo "╔══════════════════════════════════════════════╗"
echo "║   TEST 1 — MIRAN SCENARIO (normalan rad)      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1. Digni bazu i API ako ne rade (potrebni za merenje i prikaz).
echo "[1/5] Dizem bazu i API..."
docker compose up -d db api
sleep 3

# 2. Zaustavi live Edge i ocisti zaostale run-kontejnere (da ne blokiraju IP).
echo "[2/5] Zaustavljam live Edge (ako radi)..."
docker compose stop ot-edge 2>/dev/null || true
docker rm -f $(docker ps -aq --filter "name=ot-edge-ot-edge-run") 2>/dev/null || true

# 3. Ocisti bazu — ALI cuvamo baseline (poznati uredjaji) i pravila (rules.yaml,
#    to je fajl, ne baza). Brisu se samo dogadjaji, tokovi, telemetrija, inventar.
echo "[3/5] Cistim bazu (baseline i pravila ostaju)..."
docker compose exec -T db psql -U otedge -d otedge \
  -c "TRUNCATE network_flows, security_events, process_telemetry, devices, correlations, incidents RESTART IDENTITY CASCADE;" > /dev/null

# 4. Ucitaj MIRAN scenario kroz Edge (measurement — jedan prolaz).
echo "[4/5] Ucitavam mirni scenario (obrada snimka)..."
docker compose run --rm \
  -e PCAP_PATH="$PCAPS" \
  -e TELEMETRY_PATH="$TELEMETRY" \
  -e RUN_MODE=measurement \
  -e CORRELATION_ENABLED=true \
  ot-edge

# 5. Prikazi rezime detektovanog.
echo ""
echo "[5/5] Detektovano u mirnom scenariju:"
docker compose exec -T db psql -U otedge -d otedge -c "
  SELECT rule_id, severity, count(*)
  FROM security_events
  GROUP BY rule_id, severity
  ORDER BY rule_id;
"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  MIRAN SCENARIO UCITAN — otvori dashboard:    ║"
echo "║  http://localhost:5173                        ║"
echo "╚══════════════════════════════════════════════╝"