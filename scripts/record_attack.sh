#!/usr/bin/env bash
set -e

# Trajanje snimanja (podrazumevano 40s — dovoljno da napad od ~20s stane unutra)
DURATION="${1:-40}"

PCAP_OUT="tests/pcaps/attack.pcap"
TELEMETRY_OUT="tests/telemetry/attack_telemetry.jsonl"

echo "=== Snimanje NAPADA (mreža + proces), ${DURATION}s ==="

# 1. Obrisi stari attack snimak (NE dira normalni pair.*)
echo "[1/6] Brisem stari attack snimak..."
rm -f "$PCAP_OUT" "$TELEMETRY_OUT"
docker compose exec plant sh -c "rm -f /tmp/attack.pcap" 2>/dev/null || true

# 2. Pokreni pcap snimanje u plant (timeout ga sam gasi posle DURATION)
echo "[2/6] Pokrecem pcap snimanje u plant..."
docker compose exec -d plant sh -c "timeout ${DURATION} tcpdump -i any -w /tmp/attack.pcap 'tcp' 2>/dev/null"

# 3. Pokreni telemetriju u ot-edge (timeout ga sam gasi)
echo "[3/6] Pokrecem telemetriju snimanje u ot-edge..."
docker compose exec -d -e TELEMETRY_OUTPUT="$TELEMETRY_OUT" ot-edge sh -c "timeout ${DURATION} python -m edge.tools.record_telemetry 2>/dev/null"

# 4. Kratka pauza da snimanje krene, pa pusti napadaca
echo "[4/6] Cekam 3s pa pustam napadaca..."
sleep 3
docker compose run --rm rogue-sim

# 5. Cekaj da snimanje (timeout) zavrsi
echo "[5/6] Cekam da snimanje zavrsi..."
REMAINING=$((DURATION - 20))
if [ "$REMAINING" -gt 0 ]; then
  sleep "$REMAINING"
fi
sleep 3

# 6. Izvuci pcap
echo "[6/6] Izvlacim pcap..."
docker compose cp plant:/tmp/attack.pcap "$PCAP_OUT"

echo ""
echo "=== Gotovo ==="
echo "Mreza (napad):  $PCAP_OUT"
echo "Proces (napad): $TELEMETRY_OUT"
echo ""
echo "Provera:"
echo "  paketa u pcap:      $(docker compose exec plant sh -c "tcpdump -r /tmp/attack.pcap 2>/dev/null | wc -l" | tr -d '[:space:]')"
echo "  zapisa telemetrije: $(wc -l < "$TELEMETRY_OUT" 2>/dev/null | tr -d '[:space:]')"