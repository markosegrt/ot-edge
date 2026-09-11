FROM python:3.12-slim

WORKDIR /app

# tcpdump za snimanje saobracaja na SCADA tacki (HMI<->SCADA grana).
RUN apt-get update \
    && apt-get install -y --no-install-recommends tcpdump \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Klijentu treba samo modbus_client.py i scada_proxy.py.
COPY clients/ ./clients/

# Komanda i profil (hmi/scada) zadaju se u docker-compose.yml.