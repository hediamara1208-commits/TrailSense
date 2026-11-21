"""[DAWUD] Compare upper-air humidity from GFS and ECMWF IFS (both via Open-Meteo).

    python -m backend.physics.compare_models [region] [cycle_index]     (default: europe 1)

Why: GFS caps relative humidity at 100 %, so we can never see *how* supersaturated the air is,
and Jev rates every forecast as unreliable. ECMWF's IFS has a cloud scheme that allows
ice supersaturation (Tompkins et al., 2007), so its RH over ice can exceed 100 % in clear air.
If Open-Meteo passes those values through, ECMWF gives a sharper signal.

What it does, for one recorded cycle:
- takes the cycle's flagged aircraft (GFS physics) plus the region's weather grid;
- asks both models for the same hour, on the levels they share (300, 250, 200, 150 hPa);
- prints, below -40 °C: how many values are >= 95 %, == 100 %, > 100 %, the maximum,
  and a side-by-side table at the flagged aircraft.
Two calls in total (one per model), well within the free tier.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

import httpx

from backend.physics.cycle import assess_cycle
from backend.sources.recorder import REGIONS, grid_points, load_replay

URLS = {"GFS": "https://api.open-meteo.com/v1/gfs", "ECMWF": "https://api.open-meteo.com/v1/ecmwf"}
LEVELS = [300, 250, 200, 150]  # hPa, available in both models
MAX_POINTS = 100


def fetch(model: str, points: list[tuple[float, float]], ts: int) -> list[dict]:
    """Per point: {level: (T °C, RH %)} for the hour of `ts`."""
    hour = datetime.fromtimestamp(ts - ts % 3600, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M")
    hourly = [f"{v}_{p}hPa" for p in LEVELS for v in ("temperature", "relative_humidity")]
    r = httpx.get(URLS[model], timeout=30, params={
        "latitude": ",".join(f"{la:.2f}" for la, _ in points),
        "longitude": ",".join(f"{lo:.2f}" for _, lo in points),
        "hourly": ",".join(hourly), "start_hour": hour, "end_hour": hour,
    })
    r.raise_for_status()
    body = r.json()
    out = []
    for loc in body if isinstance(body, list) else [body]:
        h = loc["hourly"]
        out.append({p: (h[f"temperature_{p}hPa"][0], h[f"relative_humidity_{p}hPa"][0]) for p in LEVELS})
    return out


def summary(name: str, profiles: list[dict]) -> None:
    rh = [v[1] for prof in profiles for v in prof.values()
          if v[0] is not None and v[1] is not None and v[0] < -40]
    if not rh:
        print(f"{name:>6}: no data")
        return
    n = len(rh)
    print(f"{name:>6}: {n:4d} values below -40 °C | >=95 %: {sum(x >= 95 for x in rh):3d} | "
          f"==100 %: {sum(x == 100 for x in rh):3d} | >100 %: {sum(x > 100 for x in rh):3d} | max {max(rh):.1f} %")


def main(region: str = "europe", index: int = 1) -> None:
    data = load_replay(index, region)
    ts = data["timestamp"]
    aircraft, assessments, _ = assess_cycle(data)
    by_id = {a.icao24: a for a in aircraft}
    flagged = [by_id[r.icao24] for r in assessments if r.flagged]
    r = REGIONS[region]
    grid = grid_points(r["bbox"], r["grid_deg"])
    points = ([(a.lat, a.lon) for a in flagged] + grid)[:MAX_POINTS]
    print(f"{region}, cycle {ts} ({datetime.fromtimestamp(ts, tz=timezone.utc):%Y-%m-%d %H:%M} UTC): "
          f"{len(flagged)} flagged aircraft + {len(points) - len(flagged)} grid points\n")

    res = {}
    for model in URLS:
        try:
            res[model] = fetch(model, points, ts)
        except httpx.HTTPError as e:
            print(f"{model}: request failed ({e})")
            return
    for model, profs in res.items():
        summary(model, profs)

    print("\nAt the flagged aircraft (nearest shared level), RH % GFS -> ECMWF:")
    for i, a in enumerate(flagged[:15]):
        lvl = min(LEVELS, key=lambda p: abs(p - _fl_to_hpa(a.flight_level)))
        g, e = res["GFS"][i][lvl], res["ECMWF"][i][lvl]
        if None in g + e:
            print(f"  {a.callsign:<8} FL{a.flight_level}: missing value")
            continue
        print(f"  {a.callsign:<8} FL{a.flight_level} (~{lvl} hPa)  T {g[0]:6.1f} / {e[0]:6.1f} °C   "
              f"RH {g[1]:6.1f} -> {e[1]:6.1f} %")
    print("\nReading: if ECMWF shows values > 100 % where GFS sits at 100, we get a real supersaturation"
          " signal (and can raise the threshold above 100 %). If ECMWF also stops at 100, it is capped too."
          "\nIf ECMWF is systematically ~35 % lower than GFS at -55 °C, it is RH over water: convert with"
          " contrails.rh_ice() before comparing.")


def _fl_to_hpa(fl: int) -> float:
    from backend.physics.contrails import fl_to_pressure_hpa
    return fl_to_pressure_hpa(fl)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0] if args else "europe", int(args[1]) if len(args) > 1 else 1)
