"""H7: TrailSense cascade vs an all-LLM agent on the same ~20 recorded flights.
In VS Code: open this file, click Run > Run Python File in Dedicated Terminal.

Needs Ollama running with Granite (scripts/setup_granite.py). Costs ~1 Jev call; the all-LLM side
runs ~20 local Granite calls per cycle, on EVERY recorded cycle with a flagged flight (~7 min each;
use --one for the first cycle only). Writes data/benchmark/latest.json.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so that "backend" can be imported

from backend.benchmark.all_llm import OUT, run_all, run_benchmark  # noqa: E402

if __name__ == "__main__":
    one = "--one" in sys.argv   # default: every recorded cycle with a flagged flight
    print("Running... (the all-LLM side makes one local Granite call per flight, ~7 min per cycle)")
    r = run_benchmark() if one else run_all()
    a, c = r["all_llm"], r["trailsense"]
    print(f"\n{r['flights']} flights from {r['cycle']}, {r['flagged_by_physics']} flagged by physics\n")
    print(f"{'':18}{'all-LLM':>14}{'TrailSense':>16}")
    print(f"{'model calls':18}{a['model_calls']:>14}{c['model_calls']:>16}   (Jev {c['jev_calls']}, Granite {c['granite_calls']})")
    print(f"{'time (ms)':18}{a['ms']:>14.0f}{c['ms']:>16.0f}   (physics {c['physics_ms']} ms)")
    print(f"{'local energy (Wh)':18}{a['local_wh']:>14.4f}{c['local_wh']:>16.4f}")
    print(f"{'LLM tokens':18}{a['input_tokens'] + a['output_tokens']:>14}{'':>16}   (+ Jev {c['jev_input_tokens']} tokens)")
    print(f"\nRatios: {r['ratios']}")
    print(f"Quality: {json.dumps(r['quality'], indent=1)}")
    print(f"\nSaved to {OUT}")
