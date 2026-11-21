"""[DAWUD] Upper-air weather profiles from Open-Meteo (GFS), with a cache.

API: https://api.open-meteo.com/v1/gfs  (free, no key)
Variables: temperature_{p}hPa, relative_humidity_{p}hPa, geopotential_height_{p}hPa
for p in PRESSURE_LEVELS_HPA.

Frugality (Agent Solution judging argument):
- nearby aircraft share the same cell (WEATHER_CELL_DEG × 1 h) -> cache;
- all missing cells of a cycle go out in ONE call
  (Open-Meteo accepts several comma-separated coordinates).
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from backend import config
from backend.models import LevelWeather, WeatherProfile

log = logging.getLogger(__name__)

GFS_URL = "https://api.open-meteo.com/v1/gfs"
M_TO_FT = 3.28084
MAX_COORDS_PER_CALL = 100  # beyond this, split (URL too long)

# cell key -> (profile, fetch time)
_cache: dict[tuple, tuple[WeatherProfile, float]] = {}
# Counters read by pipeline.py to fill the Receipt
stats = {"calls": 0, "cache_hits": 0}


def cell_key(lat: float, lon: float, hour: int) -> tuple:
    """Round (lat, lon) to the nearest WEATHER_CELL_DEG cell centre, plus the UTC hour."""
    step = config.WEATHER_CELL_DEG
    return (round(round(lat / step) * step, 3), round(round(lon / step) * step, 3), hour)


def _hourly_vars() -> list[str]:
    v = []
    for p in config.PRESSURE_LEVELS_HPA:
        v += [f"temperature_{p}hPa", f"relative_humidity_{p}hPa", f"geopotential_height_{p}hPa"]
    return v


def _parse_location(loc: dict, lat: float, lon: float, hour: int) -> WeatherProfile:
    h = loc["hourly"]
    times = h["time"]
    i = min(range(len(times)), key=lambda k: abs(times[k] - hour * 3600))
    levels = []
    for p in config.PRESSURE_LEVELS_HPA:
        t = (h.get(f"temperature_{p}hPa") or [None] * len(times))[i]
        rh = (h.get(f"relative_humidity_{p}hPa") or [None] * len(times))[i]
        z = (h.get(f"geopotential_height_{p}hPa") or [None] * len(times))[i]
        if t is None or rh is None:
            continue  # level missing from the model: skip it
        levels.append(LevelWeather(pressure_hpa=p, altitude_ft=round((z or 0) * M_TO_FT),
                                   temperature_c=t, rh_pct=rh))
    return WeatherProfile(lat=lat, lon=lon, valid_time=times[i], levels=levels)


def _fetch(cells: list[tuple], hour: int) -> dict[tuple, WeatherProfile]:
    """One Open-Meteo call for a list of cells (same hour)."""
    hour_iso = datetime.fromtimestamp(hour * 3600, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M")
    params = {
        "latitude": ",".join(str(c[0]) for c in cells),
        "longitude": ",".join(str(c[1]) for c in cells),
        "hourly": ",".join(_hourly_vars()),
        "start_hour": hour_iso,
        "end_hour": hour_iso,
        "timeformat": "unixtime",
    }
    r = httpx.get(GFS_URL, params=params, timeout=20)
    r.raise_for_status()
    stats["calls"] += 1
    body = r.json()
    locs = body if isinstance(body, list) else [body]
    return {c: _parse_location(loc, c[0], c[1], hour) for c, loc in zip(cells, locs)}


def get_profiles_batch(points: list[tuple[float, float]], timestamp: int) -> dict[tuple, WeatherProfile]:
    """Profiles for a list of (lat, lon). Returns {cell_key: profile}.

    Cached cells cost nothing; the rest go out in ONE call
    (split into batches of MAX_COORDS_PER_CALL if needed).
    """
    hour = timestamp // 3600
    now = time.time()
    keys = {cell_key(lat, lon, hour) for lat, lon in points}
    out, missing = {}, []
    for k in keys:
        hit = _cache.get(k)
        if hit and now - hit[1] < config.WEATHER_TTL_S:
            out[k] = hit[0]
            stats["cache_hits"] += 1
        else:
            missing.append(k)
    for i in range(0, len(missing), MAX_COORDS_PER_CALL):
        chunk = missing[i:i + MAX_COORDS_PER_CALL]
        try:
            fetched = _fetch(chunk, hour)
        except httpx.HTTPError as e:
            log.error("Open-Meteo: %s", e)
            continue
        for k, prof in fetched.items():
            _cache[k] = (prof, now)
            out[k] = prof
    return out


def get_profile(lat: float, lon: float, timestamp: int) -> tuple[WeatherProfile, bool]:
    """Return (profile, cache_hit) for a single point. Prefer get_profiles_batch in the pipeline."""
    k = cell_key(lat, lon, timestamp // 3600)
    hits_before = stats["cache_hits"]
    prof = get_profiles_batch([(lat, lon)], timestamp).get(k)
    if prof is None:
        raise RuntimeError("Open-Meteo unavailable")
    return prof, stats["cache_hits"] > hits_before


def export_cache() -> list[dict]:
    """For recorder.py: cached profiles, JSON-serialisable."""
    from dataclasses import asdict
    return [asdict(p) for p, _ in _cache.values()]


if __name__ == "__main__":
    # Check: which levels exist, and is humidity over water or over ice?
    # Hint: if RH often exceeds 100 % at -40/-60 °C, it is already over ice.
    # If it caps around 60-70 % in cloudy areas, it is probably over water.
    import math
    logging.basicConfig(level=logging.INFO)
    pts = [(45.5, -73.5), (46.8, -71.2), (48.5, -68.5), (45.4, -75.7)]
    profs = get_profiles_batch(pts, int(time.time()))
    print(f"{stats['calls']} Open-Meteo call(s) for {len(pts)} points")
    for k, prof in profs.items():
        print(f"\nCell {k}  (levels received: {[int(l.pressure_hpa) for l in prof.levels]})")
        for l in prof.levels:
            t = l.temperature_c
            # If rh_pct were over water: RHi = RHw * e_w / e_i (Magnus, Alduchov & Eskridge 1996)
            ratio = math.exp(17.625 * t / (t + 243.04)) / math.exp(22.587 * t / (t + 273.86))
            print(f"  {int(l.pressure_hpa)} hPa  ~{l.altitude_ft:6.0f} ft  T={t:6.1f} °C  "
                  f"RH={l.rh_pct:5.1f} %  (if over water -> RHi={l.rh_pct * ratio:5.1f} %)")
