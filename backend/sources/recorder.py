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


# Recording regions. "east_canada" (config.BBOX) is the main one, saved to data/replay/.
# Extra regions go to data/regions/<name>/ and use a coarser 2° weather grid every 6 h, so that
# all regions together stay under the Open-Meteo free tier (10,000 weighted calls/day):
#   east_canada    1°, every 3 h : 325 pts -> ~6,300/day
#   north_atlantic 2°, every 6 h : 144 pts -> ~1,400/day
#   europe         2°, every 6 h :  77 pts -> ~  750/day
#   us_northeast   2°, every 6 h :  35 pts -> ~  350/day
# OpenSky: 2-4 credits per region every 5 min -> ~3,000/day for all four, under the 4,000 limit.
REGIONS = {
    "east_canada": {"bbox": config.BBOX, "grid_deg": config.RECORD_GRID_DEG,
                    "weather_s": config.RECORD_WEATHER_INTERVAL_S},
    "north_atlantic": {"bbox": {"lamin": 45.0, "lamax": 60.0, "lomin": -50.0, "lomax": -20.0},
                       "grid_deg": 2.0, "weather_s": 21600},
    "europe": {"bbox": {"lamin": 44.0, "lamax": 56.0, "lomin": -5.0, "lomax": 15.0},
               "grid_deg": 2.0, "weather_s": 21600},
    "us_northeast": {"bbox": {"lamin": 38.0, "lamax": 46.0, "lomin": -80.0, "lomax": -68.0},
                     "grid_deg": 2.0, "weather_s": 21600},
}


def region_dir(region: str) -> Path:
    return REPLAY_DIR if region == "east_canada" else REPLAY_DIR.parent / "regions" / region


def record_cycle(with_weather: bool = True, bbox: dict | None = None,
                 out_dir: Path | None = None, grid_deg: float | None = None) -> str | None:
    """Fetch aircraft (+ weather if asked) once and write <out_dir>/<timestamp>.json.

    Returns the path, or None if OpenSky returned nothing (429, network...).
    Weather is fetched for the whole grid in a few grouped calls.
    """
    bbox = bbox or config.BBOX
    out_dir = out_dir or REPLAY_DIR
    planes = opensky.fetch_aircraft(bbox)
    if not planes:
        log.warning("No cruising aircraft returned for %s (OpenSky has no receivers over the ocean)", bbox)
        return None
    ts = max(a.timestamp for a in planes)
    profiles = []
    if with_weather:
        # Fixed grid over the whole BBOX: every replayed aircraft (even one arriving later,
        # in another cell) will have a nearby profile.
        profs = weather.get_profiles_batch(grid_points(bbox, grid_deg), ts)
        profiles = [asdict(p) for p in profs.values()]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{ts}.json"
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


def replay_files(region: str = "east_canada") -> list[Path]:
    return sorted(region_dir(region).glob("*.json"), key=lambda p: int(p.stem))


def load_replay(index: int, region: str = "east_canada") -> dict:
    """Load cycle number `index` (sorted by timestamp), wrapping around at the end.

    If a cycle has no weather (recorded only every few hours), reuse the weather
    of the closest previous cycle that has it.
    """
    files = replay_files(region)
    if not files:
        raise FileNotFoundError(f"No recording in {region_dir(region)}")
    i = index % len(files)
    data = json.loads(files[i].read_text())
    j = i
    while not data.get("weather") and j > 0:
        j -= 1
        data["weather"] = json.loads(files[j].read_text()).get("weather", [])
    return data


def run_forever(region: str = "east_canada") -> None:
    """Recording loop for one region: aircraft every RECORD_S, weather at most once per its interval.

    Run one terminal per region to record several regions at the same time.
    """
    r = REGIONS[region]
    out = region_dir(region)
    last_slot = None
    log.info("Recording %s to %s (aircraft every %d s, weather every %d s). Ctrl+C to stop.",
             region, out, config.RECORD_S, r["weather_s"])
    while True:
        slot = int(time.time()) // r["weather_s"]
        need_weather = slot != last_slot
        try:
            if record_cycle(with_weather=need_weather, bbox=r["bbox"], out_dir=out,
                            grid_deg=r["grid_deg"]) and need_weather:
                last_slot = slot
        except Exception:  # never stop in the middle of the night
            log.exception("Cycle failed, carrying on")
        time.sleep(config.RECORD_S)


def snapshot(region: str) -> None:
    """One-shot capture of another region, saved to data/regions/<region>/, then scanned."""
    from backend.physics.cycle import assess_cycle
    r = REGIONS[region]
    path = record_cycle(with_weather=True, bbox=r["bbox"], out_dir=region_dir(region),
                        grid_deg=r["grid_deg"])
    if path is None:
        print("No aircraft received (quota or network).")
        return
    aircraft, assessments, stats = assess_cycle(json.loads(Path(path).read_text()))
    by_id = {a.icao24: a for a in aircraft}
    print(f"{region}: {stats['aircraft_scanned']} aircraft, {stats['flagged_by_physics']} flagged -> {path}")
    for r in assessments:
        if r.flagged:
            a = by_id[r.icao24]
            print(f"  {a.callsign:8} FL{a.flight_level}  RHi {r.current.rh_ice_pct:.0f} %  "
                  f"ISSR {r.minutes_in_issr:.0f} min  net {r.net_benefit_co2e_kg}  night={r.is_night}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Record the sky for Replay mode.")
    parser.add_argument("--once", action="store_true", help="single snapshot of --region, then scan it (default: record forever)")
    parser.add_argument("--region", default="east_canada", choices=sorted(REGIONS))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if args.once:
        snapshot(args.region)
    else:
        run_forever(args.region)
