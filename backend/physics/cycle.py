"""[DAWUD] Physics entry point for pipeline.py: one full cycle in one call.

    from backend.physics.cycle import assess_cycle, live_cycle_data
    data = load_replay(i)              # Replay mode
    data = live_cycle_data()           # Live mode (OpenSky + Open-Meteo)
    aircraft, assessments, stats = assess_cycle(data)

- aircraft     : list[Aircraft] of the cycle (for the map)
- assessments  : list[RiskAssessment], one per assessable aircraft (None results already dropped)
- stats        : {"aircraft_scanned", "flagged_by_physics", "weather_calls", "weather_cache_hits",
                  "physics_ms"} -> copy into the Receipt
"""
from __future__ import annotations

import time

from backend import config
from backend.models import Aircraft, LevelWeather, RiskAssessment, WeatherProfile
from backend.physics.contrails import assess
from backend.sources import opensky, weather
from backend.sources.recorder import grid_points, nearest_profile

MAX_PROFILE_DIST_DEG = 1.0  # beyond this, no reliable weather for the point


def to_profile(d: dict | WeatherProfile) -> WeatherProfile:
    if isinstance(d, WeatherProfile):
        return d
    return WeatherProfile(d["lat"], d["lon"], d["valid_time"], [LevelWeather(**lv) for lv in d["levels"]])


def _profile_lookup(profiles: list[dict]):
    """Function (lat, lon) -> nearest profile, or None if too far from the grid."""
    cache: dict[int, WeatherProfile] = {}

    def profile_at(lat: float, lon: float) -> WeatherProfile | None:
        p = nearest_profile(profiles, lat, lon)
        if p is None or abs(p["lat"] - lat) > MAX_PROFILE_DIST_DEG or abs(p["lon"] - lon) > MAX_PROFILE_DIST_DEG:
            return None
        return cache.setdefault(id(p), to_profile(p))
    return profile_at


def live_cycle_data() -> dict:
    """One Live cycle in the same format as a replay file (full weather grid, cached)."""
    planes = opensky.fetch_aircraft(config.BBOX)
    ts = max((a.timestamp for a in planes), default=int(time.time()))
    from dataclasses import asdict
    profs = weather.get_profiles_batch(grid_points(), ts)
    return {"timestamp": ts, "aircraft": [asdict(a) for a in planes],
            "weather": [asdict(p) for p in profs.values()]}


def assess_cycle(data: dict) -> tuple[list[Aircraft], list[RiskAssessment], dict]:
    t0 = time.perf_counter()
    calls0, hits0 = weather.stats["calls"], weather.stats["cache_hits"]
    aircraft = [a if isinstance(a, Aircraft) else Aircraft(**a) for a in data["aircraft"]]
    profile_at = _profile_lookup(data.get("weather", []))
    out = []
    for ac in aircraft:
        prof = profile_at(ac.lat, ac.lon)
        if prof is None:
            continue
        r = assess(ac, prof, profile_at=profile_at)
        if r is not None:
            out.append(r)
    stats = {
        "aircraft_scanned": len(aircraft),
        "flagged_by_physics": sum(r.flagged for r in out),
        "weather_calls": weather.stats["calls"] - calls0,
        "weather_cache_hits": weather.stats["cache_hits"] - hits0,
        "physics_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
    return aircraft, out, stats
