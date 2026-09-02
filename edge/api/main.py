from fastapi import FastAPI

from edge.api.middleware.cors import setup_cors
from edge.api.routes import alarms
from edge.api.routes import correlation
from edge.api.routes import devices
from edge.api.routes import network

app = FastAPI(title="OT Edge API")

setup_cors(app)

app.include_router(alarms.router)
app.include_router(correlation.router)
app.include_router(devices.router)
app.include_router(network.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}