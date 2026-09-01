FROM python:3.12-slim

WORKDIR /app

# Prvo samo requirements — Docker kešira ovaj sloj,
# pa se biblioteke ne instaliraju ponovo pri svakoj izmeni koda.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiraj kod simulatora. Struktura simulator/ se čuva
# da bi "from simulator.plant import ..." radilo.
COPY simulator/ ./simulator/

# Koja se komanda pokreće zadaje se u docker-compose.yml
# (isti image, dva različita servera: modbus i opcua).

RUN apt-get update && apt-get install -y tcpdump && rm -rf /var/lib/apt/lists/*