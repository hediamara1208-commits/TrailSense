"""[HEDI] Enregistrement et rejeu du ciel (mode Replay).

Pourquoi : le jury passe dimanche après-midi, en plein jour, avec un Wi-Fi incertain.
On enregistre le ciel de vendredi soir (contrails de nuit = les plus réchauffants)
et on le rejoue pendant la démo.

Format : un fichier JSON par cycle dans data/replay/, nommé <timestamp>.json,
contenant la liste des Aircraft et les WeatherProfile utilisés.
"""


def record_cycle() -> str:
    """Récupère avions + météo une fois et écrit data/replay/<timestamp>.json. Renvoie le chemin.

    TODO: à lancer en boucle (toutes les REFRESH_S secondes) vendredi soir.
    """
    raise NotImplementedError


def load_replay(index: int) -> dict:
    """Charge le cycle numéro `index` (triés par timestamp), en boucle si on dépasse la fin."""
    raise NotImplementedError
