"""[HEDI] Le cœur scientifique : ce contrail va-t-il se former, et va-t-il durer ?

Deux conditions (toutes les deux nécessaires pour un contrail persistant) :
1. Critère de Schmidt-Appleman (SAC) : le mélange gaz d'échappement + air ambiant
   devient saturé par rapport à l'eau. Dépend de la température, de la pression et
   du rendement du moteur.
   Pente de la droite de mélange : G = EI_H2O * cp * p / (eps * Q * (1 - eta))
   avec EI_H2O = 1.23 kg/kg (kérosène), cp = 1004 J/kg/K, eps = 0.622,
   Q = 43.2e6 J/kg, eta ≈ 0.3-0.4 (rendement propulsif).
   Référence : Schumann (1996), "On conditions for contrail formation from aircraft exhausts".
2. Persistance : l'air ambiant est sursaturé par rapport à la glace (RHi > 100 %).
   RHi = RHw * e_sat_eau(T) / e_sat_glace(T)  (formules de Magnus ou Sonntag).

Limite à dire au jury : les modèles météo captent mal ces zones sursaturées,
donc on affiche des probabilités, pas des certitudes.
"""
from backend.models import Aircraft, LevelRisk, RiskAssessment, WeatherProfile


def rh_ice_from_rh_water(rh_water_pct: float, temperature_c: float) -> float:
    """Convertit l'humidité relative / eau en humidité relative / glace."""
    raise NotImplementedError


def sac_satisfied(temperature_c: float, pressure_hpa: float, rh_water_pct: float,
                  eta: float = 0.35) -> bool:
    """True si le critère de Schmidt-Appleman est rempli."""
    raise NotImplementedError


def level_risk(profile: WeatherProfile, flight_level: int) -> LevelRisk:
    """Interpole le profil (en log de la pression) au niveau demandé et calcule le risque."""
    raise NotImplementedError


def is_night(lat: float, lon: float, timestamp: int) -> bool:
    """Soleil sous l'horizon ? (calcul simple de l'élévation solaire)."""
    raise NotImplementedError


def assess(aircraft: Aircraft, profile: WeatherProfile) -> RiskAssessment:
    """Risque au niveau actuel, à +20 FL et à -20 FL, plus la pénalité carburant.

    flagged = current.persistent
    """
    raise NotImplementedError
