"""Contrats de données partagés par tous les modules.

C'est LE fichier qui permet à Hedi et Dawud de travailler en parallèle :
chaque module reçoit et renvoie ces objets. Toute modification se décide à deux.
Les mêmes structures sont renvoyées en JSON par l'API (voir data/fixtures/sample_snapshot.json).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ---------- Sources (Hedi) ----------

@dataclass
class Aircraft:
    """Un avion vu par OpenSky à un instant donné."""
    icao24: str              # identifiant unique du transpondeur
    callsign: str            # ex. "ACA123"
    lat: float
    lon: float
    altitude_ft: float       # altitude barométrique, en pieds
    flight_level: int        # ex. 360 pour 36 000 ft
    heading_deg: float       # cap (sert à la règle de parité est/ouest)
    speed_kt: float
    timestamp: int           # epoch UTC, secondes


@dataclass
class LevelWeather:
    """Conditions météo à un niveau de pression."""
    pressure_hpa: float      # 300, 275, 250, 225, 200
    altitude_ft: float       # depuis la hauteur géopotentielle
    temperature_c: float
    rh_water_pct: float      # humidité relative / eau (à vérifier : convention Open-Meteo)


@dataclass
class WeatherProfile:
    """Profil vertical à une position (lat, lon) et une heure, gardé en cache par cellule."""
    lat: float
    lon: float
    valid_time: int
    levels: list[LevelWeather]


# ---------- Physique (Hedi) ----------

@dataclass
class LevelRisk:
    """Risque de contrail à un niveau de vol donné."""
    flight_level: int
    temperature_c: float
    rh_ice_pct: float
    sac_satisfied: bool      # critère de Schmidt-Appleman : le contrail se forme
    persistent: bool         # sac_satisfied ET rh_ice_pct > 100 : il dure


@dataclass
class RiskAssessment:
    """Résultat du filtre physique pour un avion : niveau actuel et options ±2 000 ft."""
    aircraft: Aircraft
    current: LevelRisk
    climb: LevelRisk | None      # FL + 20 (même parité)
    descend: LevelRisk | None    # FL - 20
    is_night: bool               # contrails de nuit = toujours réchauffants
    flagged: bool                # True si current.persistent -> envoyé à Jev
    fuel_penalty_kg: dict[str, float] = field(default_factory=dict)  # {"climb": .., "descend": ..}


# ---------- Agent (Dawud) ----------

class Action(str, Enum):
    CLIMB = "climb_2000"
    DESCEND = "descend_2000"
    MAINTAIN = "maintain"


class Route(str, Enum):
    AUTO = "auto"            # confiance >= seuil -> avis envoyé automatiquement
    HUMAN = "human_review"   # confiance < seuil -> Sophie valide


@dataclass
class Decision:
    """Sortie de Jev pour un vol signalé."""
    icao24: str
    action: Action
    confidence: float                 # 0-1, renvoyée par Jev
    persistent_warming_prob: float    # Noul
    forecast_reliability: float       # Score normalisé 0-1
    operational_feasibility: float    # Score normalisé 0-1
    route: Route


@dataclass
class Advisory:
    """Message pour la régulatrice de vol (LLM pour les 2-3 vols clés, sinon gabarit)."""
    icao24: str
    callsign: str
    text: str
    written_by: str          # "llm" ou "template"


@dataclass
class Receipt:
    """Reçu de calcul d'un cycle : la preuve de frugalité pour le jury Agent Solution."""
    aircraft_scanned: int = 0
    weather_calls: int = 0
    weather_cache_hits: int = 0
    flagged_by_physics: int = 0
    jev_calls: int = 0
    jev_input_tokens: int = 0
    llm_calls: int = 0
    llm_energy_wh: float = 0.0    # via EcoLogits
    llm_gco2e: float = 0.0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


@dataclass
class Snapshot:
    """Ce que l'API renvoie au frontend à chaque cycle."""
    mode: str                     # "live" ou "replay"
    timestamp: int
    threshold: float              # seuil d'autonomie courant
    aircraft: list[Aircraft]
    assessments: list[RiskAssessment]
    decisions: list[Decision]
    advisories: list[Advisory]
    receipt: Receipt
