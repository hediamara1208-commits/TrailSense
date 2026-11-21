"""[DAWUD] Coût carburant, CO₂, et réchauffement évité d'un changement de niveau.

Hypothèses (toutes réglables dans config.py, sourcées dans docs/hypotheses.md) :
- Type d'avion inconnu (OpenSky ne le donne pas) -> consommation de croisière générique.
- Pénalité = quelques % de la consommation pendant la déviation (~2 % dans les essais publiés).
- 3,16 kg de CO₂ par kg de kérosène brûlé.
- Réchauffement d'un contrail persistant : facteur CO2e par km, plus fort la nuit. C'est
  l'estimation la plus incertaine : on affiche une fourchette (÷/× CONTRAIL_UNCERTAINTY_FACTOR).
"""
from __future__ import annotations

from backend import config

CO2_PER_KG_FUEL = 3.16
KT_TO_KMH = 1.852


def minutes_in_issr(speed_kt: float) -> float:
    """Temps passé dans la zone sursaturée : longueur typique d'une zone / vitesse sol."""
    kmh = max(speed_kt, 1.0) * KT_TO_KMH
    return config.ISSR_TYPICAL_KM / kmh * 60.0


def fuel_penalty_kg(aircraft_type: str | None, minutes_deviated: float, direction: str) -> float:
    """Carburant supplémentaire pour voler 2 000 ft plus haut ou plus bas pendant X minutes."""
    pct = config.FUEL_PENALTY_PCT.get(direction, 2.0) / 100.0
    return config.CRUISE_FUEL_FLOW_KG_H * minutes_deviated / 60.0 * pct


def co2_kg(fuel_kg: float) -> float:
    return fuel_kg * CO2_PER_KG_FUEL


def warming_avoided_co2e_kg(minutes_in_issr: float, speed_kt: float, is_night: bool) -> float:
    """Réchauffement évité (kg CO2e) = longueur de contrail évitée × facteur jour/nuit."""
    km = minutes_in_issr / 60.0 * speed_kt * KT_TO_KMH
    return km * config.CONTRAIL_CO2E_KG_PER_KM["night" if is_night else "day"]


def warming_range_co2e_kg(central: float) -> tuple[float, float]:
    """Fourchette basse / haute à afficher à côté de la valeur centrale."""
    f = config.CONTRAIL_UNCERTAINTY_FACTOR
    return central / f, central * f


def net_benefit_co2e_kg(warming_avoided: float, fuel_penalty: float) -> float:
    """Bilan net d'une option = réchauffement évité - CO2 du carburant supplémentaire."""
    return warming_avoided - co2_kg(fuel_penalty)
