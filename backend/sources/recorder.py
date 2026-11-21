"""[DAWUD] Recording and replaying the sky (Replay mode).

Why: judging happens on Sunday, in daylight, on uncertain Wi-Fi.
We record the night sky (night contrails warm the most) and replay it.

Format: one JSON file per cycle in data/replay/<timestamp>.json
(weather covers the whole BBOX on a RECORD_GRID_DEG grid; use nearest_profile()):
  {"timestamp": int, "aircraft": [Aircraft...], "weather": [WeatherProfile...]}

Run all night:   caffeinate -is python -m backend.sources.recorder
(Ctrl+C to stop; keep the laptop plugged in, lid open.)
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
    """Fetch aircraft (+ weather if asked) once and write data/replay/<timestamp>.json.

    Returns the path, or None if OpenSky returned nothing (429, network...).
    Weather is fetched for the whole grid in a few grouped calls.
    """
    planes = opensky.fetch_aircraft(config.BBOX)
    if not planes:
        return None
    ts = max(a.timestamp for a in planes)
    profiles = []
    if with_weather:
        # Fixed grid over the whole BBOX: every replayed aircraft (even one arriving later,
        # in another cell) will have a nearby profile.
        profs = weather.get_profiles_batch(grid_points(), ts)
        profiles = [asdict(p) for p in profs.values()]
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    path = REPLAY_DIR / f"{ts}.json"
    path.write_text(json.dumps({"timestamp": ts,
                                "aircraft": [asdict(a) for a in planes],
                                "weather": profiles}))
    log.info("%s: %d aircraft, %d weather profiles", path.name, len(planes), len(profiles))
    return str(path)


def grid_points(bbox: dict | None = None, step: float | None = None) -> list[tuple[float, float]]:
    """Points of a regular grid covering the BBOX (step RECORD_GRID_DEG)."""
    bbox, step = bbox or config.BBOX, step or config.RECORD_GRID_DEG
    n_lat = int(round((bbox["lamax"] - bbox["lamin"]) / step)) + 1
    n_lon = int(round((bbox["lomax"] - bbox["lomin"]) / step)) + 1
    return [(bbox["lamin"] + i * step, bbox["lomin"] + j * step)
            for i in range(n_lat) for j in range(n_lon)]


def nearest_profile(profiles: list[dict], lat: float, lon: float) -> dict | None:
    """Weather profile (dict, as stored in a replay file) closest to an aircraft."""
    if not profiles:
        return None
    return min(profiles, key=lambda p: (p["lat"] - lat) ** 2 + (p["lon"] - lon) ** 2)


def replay_files() -> list[Path]:
    return sorted(REPLAY_DIR.glob("*.json"), key=lambda p: int(p.stem))


def load_replay(index: int) -> dict:
    """Load cycle number `index` (sorted by timestamp), wrapping around at the end.

    If a cycle has no weather (recorded only every few hours), reuse the weather
    of the closest previous cycle that has it.
    """
    files = replay_files()
    if not files:
        raise FileNotFoundError("No recording in data/replay/")
    i = index % len(files)
    data = json.loads(files[i].read_text())
    j = i
    while not data.get("weather") and j > 0:
        j -= 1
        data["weather"] = json.loads(files[j].read_text()).get("weather", [])
    return data


def run_forever() -> None:
    """Recording loop: aircraft every RECORD_S, weather at most once per RECORD_WEATHER_INTERVAL_S."""
    global _last_weather_hour
    log.info("Recording to %s (aircraft every %d s, weather every %d s). Ctrl+C to stop.",
             REPLAY_DIR, config.RECORD_S, config.RECORD_WEATHER_INTERVAL_S)
    while True:
        hour_slot = int(time.time()) // config.RECORD_WEATHER_INTERVAL_S
        need_weather = hour_slot != _last_weather_hour
        try:
            if record_cycle(with_weather=need_weather) and need_weather:
                _last_weather_hour = hour_slot
        except Exception:  # never stop in the middle of the night
            log.exception("Cycle failed, carrying on")
        time.sleep(config.RECORD_S)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    run_forever()
