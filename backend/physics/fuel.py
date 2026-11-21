"""[HEDI] Coût carburant et CO₂ d'un changement de niveau.

Hypothèses simples, à documenter dans docs/hypotheses.md :
- Pénalité ≈ quelques % de la consommation de croisière sur la portion déviée
  (ordre de grandeur des essais publiés : ~2 % sur les vols concernés).
- 3,16 kg de CO₂ par kg de kérosène brûlé.
"""

CO2_PER_KG_FUEL = 3.16


def fuel_penalty_kg(aircraft_type: str | None, minutes_deviated: float, direction: str) -> float:
    """Carburant supplémentaire estimé pour monter ou descendre de 2 000 ft pendant X minutes."""
    raise NotImplementedError


def co2_kg(fuel_kg: float) -> float:
    return fuel_kg * CO2_PER_KG_FUEL
