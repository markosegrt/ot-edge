#!/usr/bin/env bash
set -e

DB="docker compose exec -T db psql -U otedge -d otedge"

echo "=== MEASUREMENT: without correlation vs with correlation ==="
echo ""

# --- Prepare results table ---
$DB -c "CREATE TABLE IF NOT EXISTS measurements (version text, severity text, count int);" > /dev/null
$DB -c "TRUNCATE measurements;" > /dev/null

# --- PASS 1: WITHOUT correlation ---
echo "[1/2] Pass WITHOUT correlation..."
$DB -c "TRUNCATE security_events RESTART IDENTITY;" > /dev/null
CORRELATION_ENABLED=false docker compose up ot-edge --abort-on-container-exit > /dev/null 2>&1
$DB -c "INSERT INTO measurements SELECT 'without', severity, count(*) FROM security_events GROUP BY severity;" > /dev/null

# --- PASS 2: WITH correlation ---
echo "[2/2] Pass WITH correlation..."
$DB -c "TRUNCATE security_events RESTART IDENTITY;" > /dev/null
CORRELATION_ENABLED=true docker compose up ot-edge --abort-on-container-exit > /dev/null 2>&1
$DB -c "INSERT INTO measurements SELECT 'with', severity, count(*) FROM security_events GROUP BY severity;" > /dev/null

# --- Result ---
echo ""
echo "=== RESULT ==="
$DB -c "
SELECT
   severity,
   COALESCE(SUM(count) FILTER (WHERE version='without'), 0) AS without_correlation,
   COALESCE(SUM(count) FILTER (WHERE version='with'),    0) AS with_correlation
 FROM measurements
 GROUP BY severity
 ORDER BY array_position(ARRAY['CRITICAL','HIGH','MEDIUM','LOW','INFO'], severity);
"