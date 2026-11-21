"""[DAWUD] Passe la physique sur tout l'enregistrement de la nuit.

    python -m backend.physics.scan

Affiche, pour chaque cycle de data/replay/ : avions, vols signalés, nuit/jour.
Puis la distribution des humidités en dessous de -40 °C, pour trancher RH_CONVENTION :
- valeurs qui s'empilent juste sous 100 % sans jamais dépasser -> "ice" (plafonnée) ;
- valeurs > 100 % -> "ice" sans plafond ;
- jamais au-dessus de ~70 % même dans les nuages -> plutôt "water".
Sert aussi à choisir les cycles les plus "humides" pour la démo.
"""
from __future__ import annotations

import json
from collections import Counter

from backend.models import LevelWeather, WeatherProfile
from backend.physics.contrails import is_night
from backend.physics.cycle import assess_cycle
from backend.sources.recorder import replay_files


def to_profile(d: dict) -> WeatherProfile:
    return WeatherProfile(d["lat"], d["lon"], d["valid_time"], [LevelWeather(**lv) for lv in d["levels"]])


def main() -> None:
    files = replay_files()
    if not files:
        print("Aucun fichier dans data/replay/")
        return
    rh_bins: Counter = Counter()
    rh_max = 0.0
    best = []
    last_weather: list = []
    print(f"{'cycle':>12} {'heure UTC':>9} {'avions':>6} {'signalés':>8}  nuit")
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
        night = is_night(46.5, -72.0, ts)
        print(f"{f.stem:>12} {hhmm:>9} {len(data['aircraft']):>6} {len(flagged):>8}  {'oui' if night else 'non'}"
              + (f"   {', '.join(flagged[:4])}" if flagged else ""))
        best.append((len(flagged), f.stem))
    print("\nHumidité à T < -40 °C (nb de valeurs par tranche de 10 %) :")
    for b in sorted(rh_bins):
        print(f"  {b:>3}-{b + 9:<3} % : {'#' * min(rh_bins[b], 60)} {rh_bins[b]}")
    print(f"  max = {rh_max} %")
    top = sorted(best, reverse=True)[:5]
    print("\nCycles les plus intéressants pour la démo :", ", ".join(f"{s} ({n} vols)" for n, s in top))


if __name__ == "__main__":
    main()
