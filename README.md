# OT Edge

A monitoring and security system for industrial (OT) networks. It passively
observes network traffic and correlates it with process state (via OPC UA)
to detect anomalies more accurately — with fewer false alarms than a
network-only approach.

Diploma thesis project. The full plan and specification are in `docs/`.

## Structure

- `simulator/` — plant simulator (Modbus TCP + OPC UA interfaces)
- `clients/` — HMI and SCADA clients that generate traffic
- `attacker/` — attacker for test scenarios (Phase 5)
- `edge/` — the main Edge application
- `dashboard/` — React frontend (Phase 4)
- `tests/` — tests and pcap captures
- `docs/` — plan, specification, diagrams

## Running locally (without Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The simulator and clients are configured via environment variables
(see `.env.example`).

## Environment

Docker Desktop (WSL2, Ubuntu). The full lab is brought up via
`docker-compose.yml`.
