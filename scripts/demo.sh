#!/usr/bin/env bash
set -e

PCAPS="tests/pcaps/plc1.pcap,tests/pcaps/plc2.pcap,tests/pcaps/scada.pcap"

echo "=== DEMO: measurement (napadi + korelacija) -> pa vrati live ==="
echo ""

# 1. Zaustavi live Edge da oslobodi IP .50 (inace sudar adrese).
echo "[1/5] Zaustavljam live Edge..."
docker compose stop ot-edge 2>/dev/null || true
docker rm -f $(docker ps -aq --filter "name=ot-edge-ot-edge-run") 2>/dev/null || true

# 2. Ocisti stare dogadjaje (cist prikaz samo ovog snimka).
echo "[2/5] Cistim bazu (events, flows, telemetrija)..."
docker compose exec -T db psql -U otedge -d otedge \
  -c "TRUNCATE network_flows, security_events, process_telemetry RESTART IDENTITY CASCADE;" > /dev/null

# 3. Pusti measurement (napuni alarme + topologiju iz snimka).
echo "[3/5] Pustam measurement (obrada snimka)..."
docker compose run --rm \
  -e PCAP_PATH="$PCAPS" \
  -e RUN_MODE=measurement \
  -e CORRELATION_ENABLED=true \
  ot-edge

# 4. Prikazi sta je detektovano.
echo ""
echo "[4/5] Detektovani alarmi:"
docker compose exec -T db psql -U otedge -d otedge \
  -c "SELECT rule_id, severity, count(*) FROM security_events GROUP BY rule_id, severity ORDER BY rule_id;"

# 5. Vrati live Edge (dashboard opet radi uzivo za proces;
#    alarmi i topologija iz measurement-a OSTAJU jer live ne brise).
echo "[5/5] Vracam live Edge..."
docker compose up -d ot-edge

echo ""
echo "=== Gotovo. Otvori dashboard na http://localhost:5173 ==="