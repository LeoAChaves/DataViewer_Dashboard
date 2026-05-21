from pydantic import BaseModel
from typing import Any


# ── API response shapes ───────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    success: bool
    result: list[str]           # list of topics available for the session


class Reading(BaseModel):
    timestamp: int              # Unix timestamp in seconds (matches legacy API)
    data: str                   # String value (matches legacy API)


class TopicResponse(BaseModel):
    success: bool
    result: list[Reading]


class IngestPayload(BaseModel):
    session_id: str
    topic: str
    value: float


# ── Sensor topic metadata ─────────────────────────────────────────────────────
# Used by the simulator and for validation.

TOPICS: dict[str, dict[str, Any]] = {
    "Temperatura":   {"unit": "°C",    "min": -5.0,  "max": 45.0,  "base": 22.0,  "noise": 0.3},
    "Umidade":       {"unit": "%",     "min": 10.0,  "max": 100.0, "base": 65.0,  "noise": 0.5},
    "Pressao":       {"unit": "hPa",   "min": 980.0, "max": 1040.0,"base": 1013.0,"noise": 0.2},
    "Velocidade":    {"unit": "m/s",   "min": 0.0,   "max": 30.0,  "base": 3.0,   "noise": 0.4},
    "Ultravioleta":  {"unit": "W/m²",  "min": 0.0,   "max": 1200.0,"base": 0.0,   "noise": 0.0},
    "Luminosidade":  {"unit": "Lux",   "min": 0.0,   "max": 120000.0,"base":0.0,  "noise": 0.0},
    "Pluviometro":   {"unit": "mm",    "min": 0.0,   "max": 50.0,  "base": 0.0,   "noise": 0.0},
    "CO2":           {"unit": "ppm",   "min": 350.0, "max": 2000.0,"base": 420.0, "noise": 1.0},
}