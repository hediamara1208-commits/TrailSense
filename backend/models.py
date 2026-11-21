"""Data contracts shared by every module.

This is THE file that lets Hedi and Dawud work in parallel:
every module takes and returns these objects. Any change is decided by both of us.
The same structures are returned as JSON by the API (see data/fixtures/sample_snapshot.json).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ---------- Sources (Dawud) ----------

@dataclass
class Aircraft:
    """An aircraft seen by OpenSky at a given moment."""
    icao24: str              # unique transponder id
    callsign: str            # e.g. "ACA123"
    lat: float
    lon: float
    altitude_ft: float       # barometric altitude, in feet
    flight_level: int        # e.g. 360 for 36,000 ft
    heading_deg: float       # heading (used for the east/west parity rule)
    speed_kt: float
    timestamp: int           # epoch UTC, seconds


@dataclass
class LevelWeather:
    """Weather conditions at one pressure level."""
    pressure_hpa: float      # 300, 275, 250, 225, 200, 175, 150
    altitude_ft: float       # from the geopotential height
    temperature_c: float
    rh_pct: float            # relative humidity as given by GFS; convention in config.RH_CONVENTION


@dataclass
class WeatherProfile:
    """Vertical profile at one position (lat, lon) and one hour, cached per cell."""
    lat: float
    lon: float
    valid_time: int
    levels: list[LevelWeather]


# ---------- Physics (Dawud) ----------

@dataclass
class LevelRisk:
    """Contrail risk at one flight level."""
    flight_level: int
    temperature_c: float
    rh_ice_pct: float
    sac_satisfied: bool      # Schmidt-Appleman criterion: the contrail forms
    persistent: bool         # sac_satisfied AND rh_ice_pct above threshold: it lasts


@dataclass
class RiskAssessment:
    """Result of the physics filter for one aircraft: current level and ±2,000 ft options.

    Every trade-off number is computed in Python (physics, Dawud).
    Jev does NO calculation: it chooses from these numbers.
    """
    icao24: str                  # refers to Aircraft.icao24 (lighter than the full object)
    current: LevelRisk
    climb: LevelRisk | None      # FL + 20 (same parity)
    descend: LevelRisk | None    # FL - 20
    is_night: bool               # night contrails = always warming
    flagged: bool                # True if current.persistent -> sent to Jev
    minutes_in_issr: float = 0.0  # estimated time in the ice-supersaturated region at the current level
    fuel_penalty_kg: dict[str, float] = field(default_factory=dict)         # {"climb": .., "descend": ..}
    warming_avoided_co2e_kg: dict[str, float] = field(default_factory=dict) # warming avoided, in CO2e
    net_benefit_co2e_kg: dict[str, float] = field(default_factory=dict)     # avoided - CO2 of the extra fuel


# ---------- Agent (Hedi) ----------

class Action(str, Enum):
    CLIMB = "climb_2000"
    DESCEND = "descend_2000"
    MAINTAIN = "maintain"


class Route(str, Enum):
    AUTO = "auto"            # confidence >= threshold -> advisory sent automatically
    HUMAN = "human_review"   # confidence < threshold -> Sophie reviews


@dataclass
class Decision:
    """Jev's output for one flagged flight."""
    icao24: str
    action: Action
    confidence: float                 # 0-1, returned by Jev
    persistent_warming_prob: float    # Noul
    forecast_reliability: float       # Score normalised 0-1
    operational_feasibility: float    # Score normalised 0-1
    route: Route


@dataclass
class Advisory:
    """Message for the dispatcher. Writing cascade, cheapest first:
    template (free) -> local Granite (small IBM model via Ollama) -> Claude (1-2 key advisories)."""
    icao24: str
    callsign: str
    text: str
    written_by: str          # "template", "granite" or "claude"


@dataclass
class Receipt:
    """Compute receipt for one cycle: the frugality proof for the Agent Solution jury."""
    aircraft_scanned: int = 0
    weather_calls: int = 0
    weather_cache_hits: int = 0
    flagged_by_physics: int = 0
    physics_ms: float = 0.0       # physics time for the whole cycle (from assess_cycle stats)
    jev_calls: int = 0
    jev_input_tokens: int = 0
    local_llm_calls: int = 0      # Granite on the laptop (Ollama)
    local_llm_energy_wh: float = 0.0  # estimate: laptop power × call duration
    llm_calls: int = 0            # Claude (cloud)
    llm_energy_wh: float = 0.0    # via EcoLogits
    llm_gco2e: float = 0.0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


@dataclass
class Snapshot:
    """What the API returns to the frontend every cycle."""
    mode: str                     # "live" or "replay"
    timestamp: int
    threshold: float              # current autonomy threshold
    aircraft: list[Aircraft]
    assessments: list[RiskAssessment]
    decisions: list[Decision]
    advisories: list[Advisory]
    receipt: Receipt
