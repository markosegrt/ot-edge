FROM python:3.12-slim

WORKDIR /app

# scapy za zivi sniffing traži libpcap na sistemu.
RUN apt-get update && apt-get install -y libpcap0.8 && rm -rf /var/lib/apt/lists/*

# Prvo samo requirements — Docker kešira ovaj sloj,
# pa se biblioteke ne instaliraju ponovo pri svakoj izmeni koda.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod se NE kopira ovde — montira se preko volume-a u docker-compose.yml,
# da izmene koda ne traže rebuild slike.

# Koja se komanda pokreće zadaje se u docker-compose.yml.