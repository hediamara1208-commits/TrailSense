"""[DAWUD] Enregistrement et rejeu du ciel (mode Replay).

Pourquoi : le jury passe dimanche après-midi, en plein jour, avec un Wi-Fi incertain.
On enregistre le ciel de vendredi soir (contrails de nuit = les plus réchauffants)
et on le rejoue pendant la démo.

Format : un fichier JSON par cycle dans data/replay/, nommé <timestamp>.json,
contenant la liste des Aircraft et les WeatherProfile utilisés.
"""


def record_cycle() -> str:
    """Récupère avions + météo une fois et écrit data/replay/<timestamp>.json. Renvoie le chemin.

    TODO: à lancer en boucle vendredi soir, avec les limites de config.py :
    - avions toutes les RECORD_INTERVAL_S (600 s) pour ne pas épuiser les crédits OpenSky ;
    - météo toutes les RECORD_WEATHER_INTERVAL_S (3600 s), GFS ne change que toutes les 6 h.
    Gérer l'erreur 429 : attendre X-Rate-Limit-Retry-After-Seconds, ne pas planter.
    """
    raise NotImplementedError


def load_replay(index: int) -> dict:
    """Charge le cycle numéro `index` (triés par timestamp), en boucle si on dépasse la fin."""
    raise NotImplementedError
