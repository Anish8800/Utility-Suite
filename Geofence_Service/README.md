# Geofence Service

![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🚀 Overview
A FastAPI-based service that ingests vehicle GPS events, detects geofence enter/exit transitions across simple zones (circles and polygons), and exposes current zone status per vehicle. Designed for clarity, correctness, and easy operationalization.

## 📦 Setup
- Prerequisites: Python 3.11+
- Install and run:
- bash run.sh
- Visit http://localhost:8000/docs for interactive API.
- Configuration:
- Copy .env.example to .env and adjust LOG_LEVEL, EVENT_DEBOUNCE_SECONDS, ZONES_CONFIG_PATH as needed.
- Edit configs/zones.json to define your zones.

## 📦 Installation & Usage

### Prerequisites
- Python 3.11+

### Setup
```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the FastAPI server
bash run.sh
```
Configuration
Copy .env.example to .env and adjust:

LOG_LEVEL

EVENT_DEBOUNCE_SECONDS

ZONES_CONFIG_PATH

Edit configs/zones.json to define your zones.

API Testing
Visit:
http://localhost:8000/docs
to access the Swagger UI and test endpoints interactively.

## 🧪 API
- POST /events/location
- Ingest a location event and compute transitions.
- Body:
{
  "vehicle_id": "MH12AB1234",
  "position": {"lat": 18.5204, "lon": 73.8567},
  "timestamp": "2025-11-27T10:55:00Z",
  "speed_kmh": 32.5,
  "heading_deg": 180,
  "event_id": "event-uuid-optional"
}
- Response:
{
  "vehicle_id": "MH12AB1234",
  "entered": ["downtown"],
  "exited": [],
  "at": "2025-11-27T10:55:00Z",
  "position": {"lat": 18.5204, "lon": 73.8567}
}
- GET /vehicles/{vehicle_id}/status
- Response:
{
  "vehicle_id": "MH12AB1234",
  "current_zones": ["downtown"],
  "last_event_ts": "2025-11-27T10:55:00Z",
  "last_position": {"lat": 18.5204, "lon": 73.8567}
}
- GET /zones
- Returns configured zones.
- GET /health
- Basic liveness with environment and zone count.
## 📜 Curl examples
- Ingest:
curl -s -X POST http://localhost:8000/events/location \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":"MH12AB1234","position":{"lat":18.5204,"lon":73.8567},"timestamp":"2025-11-27T10:55:00Z"}'
  - Query status:
curl -s http://localhost:8000/vehicles/MH12AB1234/status
- List zones:
curl -s http://localhost:8000/zones | jq .
## 📌 Assumptions
- Zones are small enough that an equirectangular approximation is acceptable for meter-level distance near Pune.
- Enter/exit is evaluated per event; boundary is considered inside for polygons.
- Vehicles can belong to multiple overlapping zones; transitions track set differences.
- Events may arrive slightly out of order; we accept latest and update current state without historical reconciliation.
- Idempotency via optional event_id; simple debounce to avoid flapping on high-frequency updates.
## ⚙️ Design decisions and tradeoffs
- FastAPI + Shapely: Quick development, robust validation, and battle-tested geometry.
- In-memory store: Minimal footprint for the challenge; interface cleanly swaps to Redis/Postgres.
- Boundary handling: poly.contains(...) or poly.touches(...) so edges count as inside to reduce jitter; configurable in future.
- Debounce: Event-level debounce based on receive time, preventing thrash while still updating position/timestamp.
## 🛠 Operational awareness
- Logging: Structured info on transitions, exceptions captured with stack traces.
- Validation: Pydantic schema enforces lat/lon ranges; future timestamps rejected.
- Health endpoint: Simple liveness/readiness, environment echo.
- Config via env: Supports containerization and staging differentiation.
## 📈 Performance and scalability
- Stateless app per request; storage can be externalized for multi-instance scaling.
- Geometry is O(N) in number of zones; practical for “few simple zones.” For many zones, add spatial index (R-tree).
- Batching: Future endpoint could accept arrays of events for throughput.
- Async server: Uvicorn handles concurrent I/O; CPU cost limited to zone checks.
## 🧪 Edge cases handled
- Boundary inclusion to reduce oscillation.
- Idempotency guard with event_id.
- Debounce window against event storms.
- Future timestamps rejected; malformed payloads validated.
- Overlapping zones supported; multiple enters/exits in one event reported.
## 🔮 What I’d improve with more time
- Persistence: Move to Redis for state, Kafka for event log; add replay and exactly-once semantics.
- Spatial index: Build an R-tree over zone bounding boxes to accelerate candidate selection.
- Ordering: Track event logical timestamps and ignore older events that would regress state.
- Webhooks/stream: Emit transitions to a pub/sub or webhook sink; add delivery retries and DLQ.
- Observability: OpenTelemetry tracing, metrics (count transitions, latency histogram), and structured JSON logs.
- Testing: Property-based tests for geometry, load tests, and contract tests for schema.
- Boundary jitter: Add hysteresis via zone edge buffers or speed-aware smoothing.
- Security: Auth for endpoints, rate limiting per vehicle, schema-level constraints on event frequency.

---
## 📜 Dependencies
```
fastapi==0.115.2
uvicorn[standard]==0.30.0
pydantic==2.8.2
shapely==2.0.4
python-dotenv==1.0.1
```

## 📁 Project Structure

```text
Geofence_Service/
├── .venv/                        # Virtual environment (ignored via .gitignore)
│   ├── Include/
│   ├── Lib/
│   ├── Scripts/
│   └── pyvenv.cfg
├── app/                          # Core application logic
│   ├── __pycache__/              # Python cache
│   ├── config.py                 # Configuration loader
│   ├── geofence.py               # Geofence logic
│   ├── main.py                   # FastAPI entry point
│   ├── models.py                 # Pydantic models
│   ├── storage.py                # Data storage and logging
│   └── zone_loader.py            # Zone initialization logic
├── configs/                      # Zone configuration files
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
├── run.sh                        # Shell script to start the service
├── README.md                     # Documentation
```

## 🧪 Testing

Tests are located in the `tests/` directory and cover core geofence logic, API endpoints, and configuration validation.

```bash
pytest
```
## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to open a PR.

## 🧑‍💻 Author
Developed by **Anish Wadatkar** 

## 📜 License
This repository is licensed under the MIT License.