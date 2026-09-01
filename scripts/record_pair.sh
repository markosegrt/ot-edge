#!/usr/bin/env bash
set -e

# Trajanje snimanja u sekundama (podrazumevano 90)
DURATION="${1:-90}"

PCAP_OUT="tests/pcaps/pair.pcap"
TELEMETRY_OUT="tests/telemetry/pair_telemetry.jsonl"

echo "=== Snimanje usklađenog para (mreža + proces), ${DURATION}s ==="

# 1. Obriši stari par
echo "[1/6] Brisem stari par..."
rm -f "$PCAP_OUT" "$TELEMETRY_OUT"
docker compose exec plant sh -c "rm -f /tmp/pair.pcap" 2>/dev/null || true

# 2. Pokreni tcpdump u plant kontejneru (pozadina)
echo "[2/6] Pokrecem pcap snimanje u plant..."
docker compose exec -d plant tcpdump -i any -w /tmp/pair.pcap port 502

# 3. Pokreni telemetriju u Edge kontejneru (pozadina)
echo "[3/6] Pokrecem telemetriju snimanje u ot-edge..."
docker compose exec -d -e TELEMETRY_OUTPUT="$TELEMETRY_OUT" ot-edge python -m edge.tools.record_telemetry

# 4. Cekaj
echo "[4/6] Snimam ${DURATION}s (HMI pali/gasi pumpe, Modbus tece)..."
sleep "$DURATION"

# 5. Zaustavi oba
echo "[5/6] Zaustavljam snimanje..."
docker compose exec plant sh -c "pkill tcpdump" 2>/dev/null || true
docker compose exec ot-edge sh -c "pkill -f record_telemetry" 2>/dev/null || true
sleep 2

# 6. Izvuci pcap iz plant u projekat
echo "[6/6] Izvlacim pcap..."
docker compose cp plant:/tmp/pair.pcap "$PCAP_OUT"

echo ""
echo "=== Gotovo ==="
echo "Mreza:  $PCAP_OUT"
echo "Proces: $TELEMETRY_OUT"
echo ""
echo "Provera:"
echo "  paketa u pcap:  $(docker compose exec plant sh -c 'tcpdump -r /tmp/pair.pcap 2>/dev/null | wc -l' | tr -d '[:space:]')"
echo "  zapisa telemetrije: $(wc -l < "$TELEMETRY_OUT" | tr -d '[:space:]')"