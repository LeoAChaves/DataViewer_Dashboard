"""
Sensor data simulator
─────────────────────
Generates physically coherent fake readings for each topic.

Rules per sensor:
  Temperatura   — sinusoidal daily cycle + slow weather drift + small noise
  Umidade       — inversely correlated with temperature + weather events
  Pressao       — slow random walk (weather fronts), very small noise
  Velocidade    — gamma-distributed gusts, calm at night
  Ultravioleta  — bell curve peaking at solar noon, zero at night
  Luminosidade  — tracks UV but wider curve, affected by clouds
  Pluviometro   — zero most intervals; random rain events (Poisson-like)
  CO2           — base 420 ppm + human-activity peak in morning/evening
"""

import math
import random
from datetime import datetime, timezone


def _hour_fraction(dt: datetime) -> float:
    """0.0 at midnight, 1.0 at midnight next day."""
    return (dt.hour + dt.minute / 60 + dt.second / 3600) / 24


def _solar_elevation(hour_frac: float) -> float:
    """Simplified solar elevation factor [0, 1]. Peaks at noon, zero at night."""
    angle = math.pi * (hour_frac - 0.25) * 2       # shifts noon to peak
    return max(0.0, math.sin(angle))


# ── Per-sensor generators ─────────────────────────────────────────────────────

def gen_temperatura(dt: datetime, state: dict) -> float:
    h = _hour_fraction(dt)
    # Daily cycle: coldest ~05:00, warmest ~14:00
    daily = 8.0 * math.sin(2 * math.pi * (h - 0.35))
    # Slow weather drift (random walk)
    state["temp_drift"] = state.get("temp_drift", 0.0) + random.gauss(0, 0.05)
    state["temp_drift"] = max(-6.0, min(6.0, state["temp_drift"]))
    value = 22.0 + daily + state["temp_drift"] + random.gauss(0, 0.15)
    return round(max(-5.0, min(45.0, value)), 2)


def gen_umidade(dt: datetime, state: dict, temperatura: float | None = None) -> float:
    h = _hour_fraction(dt)
    # Base humidity: high at night/dawn, low at peak heat
    base = 70.0 - 20.0 * _solar_elevation(h)
    # Negative correlation with temperature
    if temperatura is not None:
        base -= (temperatura - 22.0) * 0.8
    # Rain event bonus
    rain_bonus = 20.0 if state.get("raining") else 0.0
    value = base + rain_bonus + random.gauss(0, 1.0)
    return round(max(10.0, min(100.0, value)), 2)


def gen_pressao(dt: datetime, state: dict) -> float:
    # Very slow random walk — pressure fronts move over hours/days
    state["pressao"] = state.get("pressao", 1013.0) + random.gauss(0, 0.08)
    state["pressao"] = max(980.0, min(1040.0, state["pressao"]))
    return round(state["pressao"] + random.gauss(0, 0.05), 2)


def gen_velocidade(dt: datetime, state: dict) -> float:
    h = _hour_fraction(dt)
    # Wind is calmer at night (boundary layer collapse)
    day_factor = 0.3 + 0.7 * _solar_elevation(h)
    # Gamma distribution gives realistic wind gusts (always positive)
    base = state.get("wind_base", 3.0) * day_factor
    state["wind_base"] = state.get("wind_base", 3.0) + random.gauss(0, 0.1)
    state["wind_base"] = max(0.5, min(15.0, state["wind_base"]))
    value = random.gammavariate(2.0, max(0.5, base / 2))
    return round(max(0.0, min(30.0, value)), 2)


def gen_ultravioleta(dt: datetime, state: dict) -> float:
    elev = _solar_elevation(_hour_fraction(dt))
    cloud_factor = state.get("cloud_factor", 1.0)
    value = 1100.0 * (elev ** 1.5) * cloud_factor + random.gauss(0, 3)
    return round(max(0.0, min(1200.0, value)), 2)


def gen_luminosidade(dt: datetime, state: dict) -> float:
    elev = _solar_elevation(_hour_fraction(dt))
    cloud_factor = state.get("cloud_factor", 1.0)
    # Wider curve than UV, more scattered light
    value = 110000.0 * (elev ** 1.2) * cloud_factor + random.gauss(0, 50)
    return round(max(0.0, min(120000.0, value)), 2)


def gen_pluviometro(dt: datetime, state: dict) -> float:
    """Rain occurs in events. Once it starts, it continues for a while."""
    # Decide if a rain event starts (higher chance when cloudy)
    cloud = state.get("cloud_factor", 1.0)
    start_prob = 0.003 * (1.5 - cloud)     # ~0.3% per 5-min interval normally
    stop_prob  = 0.08                        # 8% chance to stop each interval

    if state.get("raining"):
        if random.random() < stop_prob:
            state["raining"] = False
            return 0.0
        # Rain intensity: light to heavy (exponential)
        intensity = random.expovariate(1 / 3.0)
        return round(min(50.0, intensity), 3)
    else:
        if random.random() < start_prob:
            state["raining"] = True
            # Clouds thicken when it rains
            state["cloud_factor"] = max(0.0, min(1.0, random.uniform(0.0, 0.3)))
            return round(random.expovariate(1 / 2.0), 3)
        return 0.0


def gen_co2(dt: datetime, state: dict) -> float:
    h = _hour_fraction(dt)
    # Human activity peaks: morning commute (~08:00) and evening (~18:00–20:00)
    morning_peak = 80.0 * math.exp(-((h - 0.33) ** 2) / 0.005)
    evening_peak = 60.0 * math.exp(-((h - 0.78) ** 2) / 0.006)
    # Night: natural atmospheric baseline
    value = 420.0 + morning_peak + evening_peak + random.gauss(0, 2.0)
    return round(max(350.0, min(2000.0, value)), 2)


# ── Cloud dynamics (shared state) ────────────────────────────────────────────

def _update_clouds(state: dict):
    """Slow cloud cover changes (0=overcast, 1=clear)."""
    cf = state.get("cloud_factor", 1.0) + random.gauss(0, 0.02)
    state["cloud_factor"] = max(0.0, min(1.0, cf))


# ── Public interface ──────────────────────────────────────────────────────────

GENERATORS = {
    "Temperatura":  gen_temperatura,
    "Umidade":      gen_umidade,
    "Pressao":      gen_pressao,
    "Velocidade":   gen_velocidade,
    "Ultravioleta": gen_ultravioleta,
    "Luminosidade": gen_luminosidade,
    "Pluviometro":  gen_pluviometro,
    "CO2":          gen_co2,
}


def generate_readings(dt: datetime, state: dict) -> dict[str, float]:
    """
    Generate one coherent set of readings for all topics at a given datetime.
    `state` is a mutable dict that persists across calls to maintain continuity.
    """
    _update_clouds(state)

    temp = gen_temperatura(dt, state)
    readings = {
        "Temperatura":  temp,
        "Umidade":      gen_umidade(dt, state, temp),
        "Pressao":      gen_pressao(dt, state),
        "Velocidade":   gen_velocidade(dt, state),
        "Ultravioleta": gen_ultravioleta(dt, state),
        "Luminosidade": gen_luminosidade(dt, state),
        "Pluviometro":  gen_pluviometro(dt, state),
        "CO2":          gen_co2(dt, state),
    }
    return readings