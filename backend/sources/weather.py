"""[DAWUD] Profil météo en altitude depuis Open-Meteo (GFS), avec cache.

API : https://api.open-meteo.com/v1/gfs  (gratuit, sans clé)
Variables : temperature_{p}hPa, relative_humidity_{p}hPa, geopotential_height_{p}hPa
pour p dans PRESSURE_LEVELS_HPA.

Le cache est un argument central pour le jury Agent Solution : les avions proches
partagent la même cellule, donc un seul appel météo pour plusieurs avions.
"""
from backend.models import WeatherProfile


def cell_key(lat: float, lon: float, hour: int) -> tuple:
    """Arrondit (lat, lon) à WEATHER_CELL_DEG et l'heure, pour servir de clé de cache."""
    raise NotImplementedError


def get_profiles_batch(cells: list[tuple[float, float]], timestamp: int) -> dict[tuple, WeatherProfile]:
    """UN SEUL appel Open-Meteo pour toutes les cellules manquantes d'un cycle.

    Open-Meteo accepte plusieurs coordonnées séparées par des virgules
    (latitude=45.5,46.0&longitude=-73.5,-71.0). Compter 1 seul weather_call dans le Receipt :
    c'est un bon chiffre de frugalité pour le jury.
    """
    raise NotImplementedError


def get_profile(lat: float, lon: float, timestamp: int) -> tuple[WeatherProfile, bool]:
    """Renvoie (profil, cache_hit).

    TODO:
    1. Chercher cell_key dans le cache (dict en mémoire, TTL = WEATHER_TTL_S).
    2. Sinon appeler Open-Meteo (hourly, la bonne heure), construire les LevelWeather.
    3. Vérifier la convention de l'humidité (par rapport à l'eau ou à la glace ?)
       sur un profil connu, fixer config.RH_CONVENTION et le noter dans docs/hypotheses.md.
    4. Faire un appel test pour confirmer que 275, 225, 175 et 150 hPa existent bien.
    """
    raise NotImplementedError
