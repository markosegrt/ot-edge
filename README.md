# OT Edge

Sistem za nadzor i bezbednost industrijskih (OT) mreža. Pasivno prati mrežni
saobraćaj i povezuje ga sa stanjem procesa (preko OPC UA) da tačnije otkrije
anomalije — sa manje lažnih alarma nego pristup koji gleda samo mrežu.

Diplomski rad. Pun plan i specifikacija su u `docs/`.

---

# ZA DEMONSTRACIJU (najbitnije)

## Dva scenarija — mir vs napad

Sistem se demonstrira kroz dva scenarija. Svaki očisti bazu, učita snimljeni
saobraćaj i pripremi dashboard. Pokreni jedan pa drugi da vidiš razliku.

```bash
cd ~/ot-edge

# DOBAR SCENARIO (mir) — normalan rad, malo/nimalo alarma
sed -i 's/\r$//' scripts/test1.sh   # (samo prvi put — cisti Windows znakove)
chmod +x scripts/test1.sh
./scripts/test1.sh

# LOS SCENARIO (napad) — svi alarmi, korelacije, count
sed -i 's/\r$//' scripts/test2.sh
chmod +x scripts/test2.sh
./scripts/test2.sh
```

Posle svakog, otvori dashboard (vidi ispod) da vidiš rezultat.

## Dashboard

```bash
cd ~/ot-edge/dashboard
npm run dev
```

Otvori **http://localhost:5173** (OBAVEZNO localhost, NE 127.0.0.1 — zbog CORS).

Tabovi: Network (topologija), Devices, Alarms, Correlation, Baseline.

## Panel simulatora i napadača (za prikaz kako radi)

Konzolni meni — pokazuje rad PLC-ova, HMI, SCADA i napadača kroz žive logove.

```bash
cd ~/ot-edge
source venv/bin/activate
python3 simulator_screen.py
```

Biraš komponentu iz menija → objašnjenje + živi log. Opcija 5 pokreće napad.

---

# POKRETANJE SISTEMA (ručno, ako treba)

## Digni ceo lab

```bash
cd ~/ot-edge

# Svi kontejneri: simulatori + Edge + API + baza
docker compose up -d plant plant2 hmi-sim scada-sim db ot-edge api

sleep 5
docker compose ps        # provera da svi rade
```

## Napomene

- `plant` (.10) — PLC1: pumpe/nivo
- `plant2` (.11) — PLC2: ventil/pritisak
- `hmi-sim` (.20) — operaterska stanica (priča sa SCADA-om)
- `scada-sim` (.30) — nadzorna stanica (priča sa oba PLC-a)
- `db` (.40) — PostgreSQL baza
- `ot-edge` (.50) — Edge aplikacija (nadzor)
- `api` (.60) — FastAPI (dashboard čita odavde)
- `rogue-sim` (.99) — napadač (pokreće se samo za testove)

---

# KORISNE DOCKER KOMANDE

```bash
# Logovi jednog servisa (poslednjih 20 redova)
docker compose logs <ime> --tail 20
# npr: docker compose logs plant --tail 20

# Živi log (prati u realnom vremenu, Ctrl+C za izlaz)
docker compose logs -f <ime>

# Provera da API radi
curl http://localhost:8000/api/health

# Stanje svih kontejnera
docker compose ps

# Restart jednog servisa (posle izmene koda u edge/ ili api/)
docker compose restart ot-edge api

# Zaustavi sve
docker compose down
```

## Ako nešto zapne

```bash
# "Address already in use" — zaostali kontejneri drže IP:
docker rm -f $(docker ps -aq --filter "name=ot-edge") 2>/dev/null

# DNS puca u WSL:
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# Windows Python se uvukao — aktiviraj venv:
source ~/ot-edge/venv/bin/activate

# Klijent/napadač/simulator izmenjen — rebuild (nemaju mount):
docker compose build <ime>
```

---

# SNIMANJE NOVOG SAOBRAĆAJA (ako treba novi scenario)

Retko — samo ako menjaš scenario. Snima pcap + telemetriju.

```bash
# Mirni scenario (bez napadača, + nov uređaj)
./scripts/record_calm.sh

# Napad scenario (rampage: scan, sabotaža, flood)
./scripts/record_attack.sh
```

Snimci idu u `tests/pcaps/` i `tests/telemetry/`. Test skripte (test1/test2)
ih učitavaju.

---

# STRUKTURA PROJEKTA

- `simulator/` — simulator postrojenja (plant, plant2, Modbus + OPC UA)
- `clients/` — HMI i SCADA klijenti + SCADA proxy (lanac)
- `attacker/` — napadač (scan, pressure, flood, rampage)
- `edge/` — glavna Edge aplikacija (pravila, korelacija, API)
- `dashboard/` — React frontend
- `scripts/` — test1, test2, record_calm, record_attack
- `simulator_screen.py` — konzolni panel za demo
- `tests/` — pcap snimci i telemetrija
- `docs/` — plan, specifikacija

---

# INSTALACIJA (prvi put)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Okruženje: Docker Desktop (WSL2, Ubuntu). Lab se diže preko `docker-compose.yml`.