"""[DAWUD] Run the physics over the whole overnight recording.

    python -m backend.physics.scan [region]           (default: east_canada)
    python -m backend.physics.scan [region] --sweep   threshold sensitivity (W5)

Prints, for each cycle in data/replay/: aircraft, flagged flights, night/day.
Then the humidity distribution below -40 °C, to settle RH_CONVENTION:
- values piling up just below 100 % and never above -> "ice" (capped);
- values > 100 % -> "ice" without cap;
- never above ~70 % even in clouds -> rather "water".
Also used to pick the most "humid" cycles for the demo.
"""
from __future__ import annotations

import json
from collections import Counter

from backend import config
from backend.models import LevelWeather, WeatherProfile
from backend.physics.contrails import is_night
from backend.physics.cycle import assess_cycle
from backend.sources.recorder import replay_files


def to_profile(d: dict) -> WeatherProfile:
    return WeatherProfile(d["lat"], d["lon"], d["valid_time"], [LevelWeather(**lv) for lv in d["levels"]])


def main(region: str = "east_canada") -> None:
    files = replay_files(region)
    if not files:
        print("No file in data/replay/")
        return
    rh_bins: Counter = Counter()
    rh_max = 0.0
    best = []
    last_weather: list = []
    print(f"{'cycle':>12} {'UTC time':>9} {'aircraft':>8} {'flagged':>7}  night")
    for f in files:
        data = json.loads(f.read_text())
        weather = data.get("weather") or last_weather
        last_weather = weather
        for prof in data.get("weather", []):
            for lv in prof["levels"]:
                if lv["temperature_c"] < -40:
                    rh_bins[min(int(lv["rh_pct"] // 10) * 10, 120)] += 1
                    rh_max = max(rh_max, lv["rh_pct"])
        data["weather"] = weather
        aircraft, assessments, _ = assess_cycle(data)
        by_id = {a.icao24: a for a in aircraft}
        flagged = [f"{by_id[r.icao24].callsign} FL{by_id[r.icao24].flight_level}"
                   for r in assessments if r.flagged]
        ts = data["timestamp"]
        hhmm = f"{ts // 3600 % 24:02d}:{ts // 60 % 60:02d}"
        lat0, lon0 = (aircraft[0].lat, aircraft[0].lon) if aircraft else (46.5, -72.0)
        night = is_night(lat0, lon0, ts)
        print(f"{f.stem:>12} {hhmm:>9} {len(data['aircraft']):>8} {len(flagged):>7}  {'yes' if night else 'no'}"
              + (f"   {', '.join(flagged[:4])}" if flagged else ""))
        best.append((len(flagged), f.stem, night))
    print("\nHumidity at T < -40 °C (number of values per 10 % bin):")
    for b in sorted(rh_bins):
        print(f"  {b:>3}-{b + 9:<3} % : {'#' * min(rh_bins[b], 60)} {rh_bins[b]}")
    print(f"  max = {rh_max} %")
    top = sorted(best, reverse=True)[:5]
    print("\nBest cycles for the demo:", ", ".join(f"{s} ({n} flights)" for n, s, _ in top))
    day = [(n, s) for n, s, night in sorted(best, reverse=True) if n and not night][:5]
    print("Best DAYTIME cycles:", ", ".join(f"{s} ({n} flights)" for n, s in day) or "none yet")


def load_cycles(region: str) -> list[dict]:
    """All cycles of a region, each with weather (reusing the last recorded one)."""
    cycles, last_weather = [], []
    for f in replay_files(region):
        data = json.loads(f.read_text())
        last_weather = data.get("weather") or last_weather
        data["weather"] = last_weather
        cycles.append(data)
    return cycles


def sweep(region: str = "east_canada", thresholds=(90.0, 92.5, 95.0, 97.5, 100.0)) -> None:
    """How many flights are flagged as the persistence threshold RHi changes."""
    cycles = load_cycles(region)
    if not cycles:
        print("No recording for", region)
        return
    default = config.RHI_THRESHOLD
    print(f"Threshold sensitivity, {region}: {len(cycles)} cycles, "
          f"{sum(len(c['aircraft']) for c in cycles)} aircraft positions\n")
    print(f"{'RHi threshold':>13} {'flagged pos.':>12} {'unique flights':>14} {'cycles with >=1':>15}  {'net CO2e avoided (t)':>20}")
    try:
        for th in thresholds:
            config.RHI_THRESHOLD = th
            n_pos, flights, n_cyc, benefit = 0, set(), 0, 0.0
            for data in cycles:
                aircraft, assessments, _ = assess_cycle(data)
                by_id = {a.icao24: a for a in aircraft}
                hits = [r for r in assessments if r.flagged]
                n_pos += len(hits)
                n_cyc += bool(hits)
                flights |= {by_id[r.icao24].callsign for r in hits}
                for r in hits:
                    benefit += max(max(r.net_benefit_co2e_kg.values(), default=0.0), 0.0)
            mark = "  <- default" if th == default else ""
            print(f"{th:>12.1f}% {n_pos:>12} {len(flights):>14} {n_cyc:>15}  {benefit / 1000:>20.1f}{mark}")
    finally:
        config.RHI_THRESHOLD = default
    print("\nGFS caps RH at 100 % and underestimates supersaturation, so 95 % is a tuning choice;"
          " the result is a ranking of candidates, not an exact count.")


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    region = args[0] if args else "east_canada"
    sweep(region) if "--sweep" in sys.argv else main(region)
