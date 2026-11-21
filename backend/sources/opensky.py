"""[DAWUD] Avions en direct depuis OpenSky.

API : GET https://opensky-network.org/api/states/all?lamin=..&lamax=..&lomin=..&lomax=..
Anonyme = état actuel seulement, résolution 10 s, crédits limités (erreur 429 si dépassé).
Doc : https://openskynetwork.github.io/opensky-api/rest.html
"""
from backend.models import Aircraft


def fetch_aircraft(bbox: dict) -> list[Aircraft]:
    """Renvoie les avions en croisière dans la boîte.

    TODO:
    1. Appeler l'API avec httpx (timeout court, gérer 429 -> renvoyer liste vide + log).
    2. Convertir chaque "state vector" en Aircraft (baro_altitude est en MÈTRES -> pieds).
    3. Garder seulement MIN_FLIGHT_LEVEL <= FL <= MAX_FLIGHT_LEVEL et on_ground == False.
    """
    raise NotImplementedError
