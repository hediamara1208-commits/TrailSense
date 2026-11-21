"""[DAWUD] Coût carburant et CO₂ d'un changement de niveau.

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


def warming_avoided_co2e_kg(minutes_in_issr: float, speed_kt: float, is_night: bool) -> float:
    """Réchauffement évité en CO2e si l'avion sort de la zone sursaturée.

    Hypothèse à sourcer et afficher clairement (docs/hypotheses.md) :
    longueur de contrail évitée (km) = minutes_in_issr * vitesse
    × un facteur CO2e par km de contrail persistant (ordre de grandeur tiré de la littérature, CoCiP),
    plus élevé la nuit (le contrail ne fait que piéger la chaleur).
    C'est l'estimation la plus incertaine du projet : la présenter avec une fourchette.
    """
    raise NotImplementedError


def net_benefit_co2e_kg(warming_avoided: float, fuel_penalty: float) -> float:
    """Bilan net d'une option = réchauffement évité - CO2 du carburant supplémentaire."""
    return warming_avoided - co2_kg(fuel_penalty)
