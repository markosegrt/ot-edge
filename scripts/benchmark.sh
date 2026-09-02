#!/usr/bin/env bash
set -e

RUNS=3
echo "=== BENCHMARK: obrada pcap-a, ${RUNS} prolaza ==="
echo ""

declare -a times mems cpus
packets=""
flows=""
writes=""

for i in $(seq 1 "$RUNS"); do
    echo "[$i/$RUNS] prolaz..."
    out=$(docker compose run --rm ot-edge python -m edge.main 2>/dev/null)

    # Broj paketa/tokova/upisa (isti u svakom prolazu — deterministicki ulaz)
    line=$(echo "$out" | grep "PcapReader:")
    packets=$(echo "$line" | grep -oP 'procitano \K[0-9]+')
    flows=$(echo "$line" | grep -oP '\K[0-9]+(?= tokova)')
    writes=$(echo "$line" | grep -oP '\K[0-9]+(?= upisa)')

    t=$(echo "$out" | grep -oP 'obrada_sekundi: \K[0-9.]+')
    m=$(echo "$out" | grep -oP 'vrsna_memorija_mb: \K[0-9.]+')
    c=$(echo "$out" | grep -oP 'cpu_sekundi: \K[0-9.]+')

    times+=("$t")
    mems+=("$m")
    cpus+=("$c")
    echo "     obrada=${t}s  memorija=${m}MB  cpu=${c}s"
done

# Prosek preko awk
avg() {
    printf '%s\n' "$@" | awk '{s+=$1; n++} END {printf "%.3f", s/n}'
}

avg_t=$(avg "${times[@]}")
avg_m=$(avg "${mems[@]}")
avg_c=$(avg "${cpus[@]}")

# Propusnost = paketi / prosecno vreme obrade
throughput=$(awk -v p="$packets" -v t="$avg_t" 'BEGIN {printf "%.0f", p/t}')

echo ""
echo "=== REZULTAT (prosek ${RUNS} prolaza) ==="
echo ""
echo "Lanac smanjenja:"
echo "  paketi:  $packets"
echo "  tokovi:  $flows"
echo "  upisi:   $writes"
echo ""
echo "Performanse:"
echo "  prosecno vreme obrade:  ${avg_t} s"
echo "  propusnost:             ${throughput} paketa/s"
echo "  vrsna memorija:         ${avg_m} MB"
echo "  prosecno CPU vreme:     ${avg_c} s"