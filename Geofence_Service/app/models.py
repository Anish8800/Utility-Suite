from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime

class LatLon(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)

class LocationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vehicle_id: str = Field(..., min_length=1)
    position: LatLon
    timestamp: datetime
    speed_kmh: Optional[float] = Field(None, ge=0.0)
    heading_deg: Optional[float] = Field(None, ge=0.0, le=360.0)
    event_id: Optional[str] = Field(None, description="Optional unique id to ensure idempotency")

class Zone(BaseModel):
    id: str
    name: str
    type: Literal["circle", "polygon"]
    center: Optional[LatLon] = None
    radius_m: Optional[float] = None
    points: Optional[List[LatLon]] = None

class VehicleStatus(BaseModel):
    vehicle_id: str
    current_zones: List[str]
    last_event_ts: Optional[datetime] = None
    last_position: Optional[LatLon] = None

class Transition(BaseModel):
    vehicle_id: str
    entered: List[str]
    exited: List[str]
    at: datetime
    position: LatLon