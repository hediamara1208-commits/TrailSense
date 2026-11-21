"""[DAWUD] Enregistrement et rejeu du ciel (mode Replay).

Pourquoi : le jury passe dimanche, en plein jour, avec un Wi-Fi incertain.
On enregistre le ciel de nuit (contrails de nuit = les plus réchauffants) et on le rejoue.

Format : un fichier JSON par cycle dans data/replay/<timestamp>.json
(la météo couvre toute la BBOX sur une grille RECORD_GRID_DEG ; utiliser nearest_profile()) :
  {"timestamp": int, "aircraft": [Aircraft...], "weather": [WeatherProfile...]}

Lancer toute la nuit :   python -m backend.sources.recorder
(Ctrl+C pour arrêter ; laisser le portable branché, veille désactivée.)
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path

from backend import config
from backend.sources import opensky, weather

log = logging.getLogger(__name__)

REPLAY_DIR = Path(__file__).resolve().parents[2] / "data" / "replay"
_last_weather_hour: int | None = None


def record_cycle(with_weather: bool = True) -> str | None:
    """Récupère avions (+ météo si demandé) une fois et écrit data/replay/<timestamp>.json.

    Renvoie le chemin, ou None si OpenSky n'a rien renvoyé (429, réseau...).
    La météo est récupérée en UN appel groupé pour toutes les cellules des avions.
    """
    planes = opensky.fetch_aircraft(config.BBOX)
    if not planes:
        return None
    ts = max(a.timestamp for a in planes)
    profiles = []
    if with_weather:
        # Grille fixe sur toute la BBOX : chaque avion rejoué (même arrivé plus tard
        # dans l'heure, dans une autre cellule) aura un profil proche.
        profs = weather.get_profiles_batch(grid_points(), ts)
        profiles = [asdict(p) for p in profs.values()]
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    path = REPLAY_DIR / f"{ts}.json"
    path.write_text(json.dumps({"timestamp": ts,
                                "aircraft": [asdict(a) for a in planes],
                                "weather": profiles}))
    log.info("%s : %d avions, %d profils météo", path.name, len(planes), len(profiles))
    return str(path)


def grid_points(bbox: dict | None = None, step: float | None = None) -> list[tuple[float, float]]:
    """Points d'une grille régulière couvrant la BBOX (pas RECORD_GRID_DEG)."""
    bbox, step = bbox or config.BBOX, step or config.RECORD_GRID_DEG
    n_lat = int(round((bbox["lamax"] - bbox["lamin"]) / step)) + 1
    n_lon = int(round((bbox["lomax"] - bbox["lomin"]) / step)) + 1
    return [(bbox["lamin"] + i * step, bbox["lomin"] + j * step)
            for i in range(n_lat) for j in range(n_lon)]


def nearest_profile(profiles: list[dict], lat: float, lon: float) -> dict | None:
    """Profil météo (dict, tel que dans un fichier de replay) le plus proche d'un avion."""
    if not profiles:
        return None
    return min(profiles, key=lambda p: (p["lat"] - lat) ** 2 + (p["lon"] - lon) ** 2)


def replay_files() -> list[Path]:
    return sorted(REPLAY_DIR.glob("*.json"), key=lambda p: int(p.stem))


def load_replay(index: int) -> dict:
    """Charge le cycle numéro `index` (triés par timestamp), en boucle si on dépasse la fin.

    Si un cycle n'a pas de météo (enregistrée seulement toutes les heures), on reprend
    celle du cycle précédent le plus proche qui en a.
    """
    files = replay_files()
    if not files:
        raise FileNotFoundError("Aucun enregistrement dans data/replay/")
    i = index % len(files)
    data = json.loads(files[i].read_text())
    j = i
    while not data.get("weather") and j > 0:
        j -= 1
        data["weather"] = json.loads(files[j].read_text()).get("weather", [])
    return data


def run_forever() -> None:
    """Boucle d'enregistrement : avions toutes les RECORD_S, météo au plus une fois par heure."""
    global _last_weather_hour
    log.info("Enregistrement dans %s (avions / %d s, météo / %d s). Ctrl+C pour arrêter.",
             REPLAY_DIR, config.RECORD_S, config.RECORD_WEATHER_INTERVAL_S)
    while True:
        hour_slot = int(time.time()) // config.RECORD_WEATHER_INTERVAL_S
        need_weather = hour_slot != _last_weather_hour
        try:
            if record_cycle(with_weather=need_weather) and need_weather:
                _last_weather_hour = hour_slot
        except Exception:  # on ne s'arrête jamais en pleine nuit
            log.exception("Cycle raté, on continue")
        time.sleep(config.RECORD_S)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    run_forever()
