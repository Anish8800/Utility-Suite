import logging
from fastapi import FastAPI, HTTPException
from fastapi import Body
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime

from .models import LocationEvent, VehicleStatus, Transition, Zone
from .zone_loader import load_zones
from .geofence import zones_for_point
from .storage import InMemoryStore
from .config import LOG_LEVEL, EVENT_DEBOUNCE_SECONDS, ENV

# Logger
logger = logging.getLogger("geofence")
logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

app = FastAPI(title="Geofence Service", version="0.1.0")

ZONES: List[Zone] = load_zones()
STORE = InMemoryStore(debounce_seconds=EVENT_DEBOUNCE_SECONDS)

@app.get("/health")
def health():
    return {"status": "ok", "env": ENV, "zones": len(ZONES)}

@app.get("/zones")
def list_zones():
    return [z.model_dump() for z in ZONES]

@app.get("/vehicles/{vehicle_id}/status", response_model=VehicleStatus)
def vehicle_status(vehicle_id: str):
    v = STORE.get(vehicle_id)
    return VehicleStatus(
        vehicle_id=vehicle_id,
        current_zones=v.current_zones,
        last_event_ts=v.last_event_ts,
        last_position=v.last_position
    )

@app.post("/events/location", response_model=Transition)
def ingest_location(event: LocationEvent = Body(...)):
    try:
        if event.timestamp > datetime.utcnow():
            raise HTTPException(status_code=400, detail="Timestamp cannot be in the future.")

        current_zone_ids = zones_for_point(ZONES, event.position)
        prev = STORE.get(event.vehicle_id)
        prev_zone_ids = set(prev.current_zones)
        curr_zone_ids = set(current_zone_ids)

        entered = sorted(list(curr_zone_ids - prev_zone_ids))
        exited = sorted(list(prev_zone_ids - curr_zone_ids))

        STORE.upsert(
            vehicle_id=event.vehicle_id,
            zones=current_zone_ids,
            ts=event.timestamp,
            position=event.position.model_dump(),
            event_id=event.event_id
        )

        if entered or exited:
            logger.info(
                f"vehicle={event.vehicle_id} entered={entered} exited={exited} "
                f"lat={event.position.lat} lon={event.position.lon} ts={event.timestamp.isoformat()}"
            )

        return Transition(
            vehicle_id=event.vehicle_id,
            entered=entered,
            exited=exited,
            at=event.timestamp,
            position=event.position
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to process event.")
        raise HTTPException(status_code=500, detail="Internal error")