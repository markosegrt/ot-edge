#!/usr/bin/env bash
set -e

TELEMETRY_OUT="tests/telemetry/pair_telemetry.jsonl"
PCAP_OUT="tests/pcaps/pair.pcap"

# Trajanje snimanja: 6 upisa x 70s = 350s napada + margina za povezivanje i rep.
TRAJANJE=370

echo "=== Snimanje merne serije: napad + proces + mreza (~6.5 min) ==="
echo "HMI ne dira pumpe (HMI_VEROVATNOCA_KOMANDE=0). Jedini koji pise je napadac."
echo ""

# 1. Podigni lab sa ucutkanim HMI. scada cita, plant kuca, db radi.
echo "[1/6] Dizem lab (plant, hmi ucutkan, scada, db)..."
docker compose up -d plant scada-sim db
HMI_VEROVATNOCA_KOMANDE=0 docker compose up -d --force-recreate hmi-sim
sleep 5

# 2. Obrisi stari par.
echo "[2/6] Brisem stari par..."
docker compose run --rm ot-edge sh -c "rm -f /app/$PCAP_OUT /app/$TELEMETRY_OUT" 2>/dev/null || true
docker compose exec plant sh -c "rm -f /tmp/pair.pcap" 2>/dev/null || true

# 3. Pokreni tcpdump u plant kontejneru sa ugradjenim limitom trajanja.
#    -G TRAJANJE + -W 1 = snimi jedan fajl duzine TRAJANJE sekundi pa stani.
echo "[3/6] Pokrecem pcap snimanje u plant (limit ${TRAJANJE}s)..."
docker compose exec -d plant tcpdump -i any -w /tmp/pair.pcap -G "$TRAJANJE" -W 1 port 502

# 4. Pokreni telemetriju kao ZASEBAN kontejner (Edge servis ne stoji uzivo).
#    timeout ga sam ugasi posle TRAJANJE sekundi.
echo "[4/6] Pokrecem telemetriju snimanje (zaseban kontejner)..."
docker compose run --rm -d \
  -e TELEMETRY_OUTPUT="$TELEMETRY_OUT" \
  ot-edge timeout "$TRAJANJE" python -m edge.tools.record_telemetry
sleep 3

# 5. Pusti napadaca. Blokira dok ne zavrsi svih 6 upisa (~350s).
echo "[5/6] Pustam napadaca (traje ~6 min, 6 upisa x 70s)..."
docker compose run --rm -e ATTACK=write rogue-sim

# 6. Sacekaj da tcpdump/telemetrija dostignu svoj limit, pa izvuci pcap.
echo "[6/6] Cekam kraj snimanja i izvlacim pcap..."
sleep 20
docker compose cp plant:/tmp/pair.pcap "$PCAP_OUT"

echo ""
echo "=== Gotovo ==="
echo "  paketa u pcap:      $(docker compose exec plant sh -c 'tcpdump -r /tmp/pair.pcap 2>/dev/null | wc -l' | tr -d '[:space:]')"
echo "  zapisa telemetrije: $(wc -l < "$TELEMETRY_OUT" 2>/dev/null | tr -d '[:space:]')"