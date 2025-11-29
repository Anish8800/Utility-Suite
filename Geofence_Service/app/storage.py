import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from .models import VehicleStatus

@dataclass
class VehicleEntry:
    current_zones: List[str]
    last_event_ts: Optional[datetime]
    last_position: Optional[dict]
    last_event_id: Optional[str]
    last_event_recv_epoch: float

class InMemoryStore:
    def __init__(self, debounce_seconds: int = 2):
        self._vehicles: Dict[str, VehicleEntry] = {}
        self._debounce_seconds = debounce_seconds

    def get(self, vehicle_id: str) -> VehicleEntry:
        return self._vehicles.get(vehicle_id, VehicleEntry([], None, None, None, 0.0))

    def upsert(self, vehicle_id: str, zones: List[str], ts: datetime, position: dict, event_id: Optional[str]) -> VehicleEntry:
        now = time.time()
        prev = self._vehicles.get(vehicle_id)
        if prev and event_id and prev.last_event_id == event_id:
            return prev  # idempotent
        if prev and now - prev.last_event_recv_epoch < self._debounce_seconds:
            # too soon since last event — keep zones but update timestamp/position
            prev.last_event_ts = ts
            prev.last_position = position
            prev.last_event_recv_epoch = now
            prev.last_event_id = event_id or prev.last_event_id
            self._vehicles[vehicle_id] = prev
            return prev

        entry = VehicleEntry(
            current_zones=zones,
            last_event_ts=ts,
            last_position=position,
            last_event_id=event_id,
            last_event_recv_epoch=now
        )
        self._vehicles[vehicle_id] = entry
        return entry