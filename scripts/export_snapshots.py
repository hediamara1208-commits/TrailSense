"""Exports a few real recorded cycles as static JSON, for the published Lovable demo (task T1).

In VS Code: open this file, click Run > Run Python File in Dedicated Terminal.

- Scans every recording (data/replay/ = east_canada, data/regions/<name>/ = Dawud's other regions).
- Keeps the cycles with the most flagged flights, plus one dry cycle (honesty: most of the sky is fine).
- Runs the FULL pipeline on each: physics, Jev (real calls if TYPESAFE_API_KEY is in .env, else the
  fallback rule), advisories. Jev is called only for the chosen cycles: ~1 call per flagged flight.
- Writes data/exports/snapshots/index.json + one <region>_<timestamp>.json per cycle,
  ready to copy into the Lovable app's public/snapshots/ folder.

Options: --max 8 (cycles)  --regions east_canada,north_atlantic,europe  --no-jev
"""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so that "backend" can be imported

from backend import config  # noqa: E402
from backend.agent import pipeline  # noqa: E402
from backend.physics.cycle import assess_cycle  # noqa: E402
from backend.sources.recorder import REGIONS, replay_files  # noqa: E402

OUT = ROOT / "data" / "exports" / "snapshots"


def load_with_weather(files: list[Path], i: int) -> dict:
    """Cycle i, reusing the weather of the closest previous cycle that has it (like load_replay)."""
    data = json.loads(files[i].read_text())
    j = i
    while not data.get("weather") and j > 0:
        j -= 1
        data["weather"] = json.loads(files[j].read_text()).get("weather", [])
    return data


def candidates(regions: list[str]) -> list[tuple[int, str, int]]:
    """(flagged, region, index) for every recorded cycle: physics only, free and fast."""
    out = []
    for region in regions:
        files = replay_files(region)
        for i in range(len(files)):
            data = load_with_weather(files, i)
            if not data.get("weather"):
                continue
            _, _, stats = assess_cycle(data)
            out.append((stats["flagged_by_physics"], region, i))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--regions", default="east_canada,north_atlantic,europe,us_northeast")
    ap.add_argument("--no-jev", action="store_true", help="use the fallback rule (no Jev credits)")
    args = ap.parse_args()
    if args.no_jev:
        config.USE_JEV = False

    regions = [r for r in args.regions.split(",") if r in REGIONS]
    cands = candidates(regions)
    if not cands:
        print("No recording found. Run scripts/record_once.py first (or get Dawud's cycles).")
        return
    flagged = sorted((c for c in cands if c[0] > 0), reverse=True)[: args.max - 1]
    dry = [c for c in cands if c[0] == 0][:1]
    chosen = flagged + dry
    print(f"{len(cands)} cycles scanned, {sum(1 for c in cands if c[0])} with flagged flights; exporting {len(chosen)}.")

    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for n_flagged, region, i in chosen:
        data = load_with_weather(replay_files(region), i)
        snap = pipeline.compute_from_data(data, "replay", config.DEFAULT_THRESHOLD)
        d = json.loads(json.dumps(asdict(snap), default=lambda o: o.value))  # enums -> strings
        name = f"{region}_{snap.timestamp}.json"
        d["source"] = f"replay {region} {snap.timestamp}"
        d["region"] = region
        d["bbox"] = REGIONS[region]["bbox"]
        (OUT / name).write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")
        deciders = sorted({x["decided_by"] for x in d["decisions"]})
        index.append({"file": name, "region": region, "timestamp": snap.timestamp,
                      "aircraft": len(d["aircraft"]), "flagged": n_flagged, "decided_by": deciders})
        print(f"  {name}: {len(d['aircraft'])} aircraft, {n_flagged} flagged, "
              f"{d['receipt']['jev_calls']} Jev call(s), decided by {deciders or '-'}")
    (OUT / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    print(f"\nWritten to {OUT}")


if __name__ == "__main__":
    main()
