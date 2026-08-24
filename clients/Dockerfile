FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Klijentu treba samo modbus_client.py.
COPY clients/ ./clients/

# Komanda i profil (hmi/scada) zadaju se u docker-compose.yml.
