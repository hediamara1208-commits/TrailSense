"""[DAWUD] Fuel cost, CO₂, and avoided warming of a level change.

Assumptions (all tunable in config.py, sourced in docs/hypotheses.md):
- Aircraft type unknown (OpenSky does not provide it) -> generic cruise fuel flow.
- Penalty = a few % of fuel burn during the deviation (~2 % in published trials).
- 3.16 kg of CO₂ per kg of kerosene burned.
- Warming of a persistent contrail: CO2e factor per km, higher at night. This is
  the most uncertain estimate: we show a range (÷/× CONTRAIL_UNCERTAINTY_FACTOR).
"""
from __future__ import annotations

from backend import config

CO2_PER_KG_FUEL = 3.16
KT_TO_KMH = 1.852


def minutes_in_issr(speed_kt: float) -> float:
    """Time spent in the supersaturated region: typical region length / ground speed."""
    kmh = max(speed_kt, 1.0) * KT_TO_KMH
    return config.ISSR_TYPICAL_KM / kmh * 60.0


def fuel_penalty_kg(aircraft_type: str | None, minutes_deviated: float, direction: str) -> float:
    """Extra fuel to fly 2,000 ft higher or lower for X minutes."""
    pct = config.FUEL_PENALTY_PCT.get(direction, 2.0) / 100.0
    return config.CRUISE_FUEL_FLOW_KG_H * minutes_deviated / 60.0 * pct


def co2_kg(fuel_kg: float) -> float:
    return fuel_kg * CO2_PER_KG_FUEL


def warming_avoided_co2e_kg(minutes_in_issr: float, speed_kt: float, is_night: bool) -> float:
    """Avoided warming (kg CO2e) = avoided contrail length × day/night factor."""
    km = minutes_in_issr / 60.0 * speed_kt * KT_TO_KMH
    return km * config.CONTRAIL_CO2E_KG_PER_KM["night" if is_night else "day"]


def warming_range_co2e_kg(central: float) -> tuple[float, float]:
    """Low / high range to show next to the central value."""
    f = config.CONTRAIL_UNCERTAINTY_FACTOR
    return central / f, central * f


def net_benefit_co2e_kg(warming_avoided: float, fuel_penalty: float) -> float:
    """Net benefit of an option = avoided warming - CO2 of the extra fuel."""
    return warming_avoided - co2_kg(fuel_penalty)
