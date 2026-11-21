"""T3: downloads IBM Granite into Ollama (~2.1 GB, once) and tests one advisory on a real flagged flight.
In VS Code: open this file, click Run > Run Python File in Dedicated Terminal.

Needs the Ollama app running (it starts with Windows; otherwise open "Ollama" from the Start menu).
"""
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so that "backend" can be imported

from backend import config  # noqa: E402
from backend.agent import fallback, writer  # noqa: E402
from backend.physics.cycle import assess_cycle  # noqa: E402
from backend.sources.recorder import load_replay, replay_files  # noqa: E402


def pull() -> None:
    print(f"Downloading {config.GRANITE_MODEL} (only the first time)...")
    last = ""
    with httpx.stream("POST", f"{config.OLLAMA_URL}/api/pull", json={"model": config.GRANITE_MODEL},
                      timeout=None) as r:
        for line in r.iter_lines():
            if not line:
                continue
            msg = json.loads(line)
            if "error" in msg:
                raise RuntimeError(msg["error"])
            status = msg.get("status", "")
            if msg.get("total"):
                pct = 100 * msg.get("completed", 0) / msg["total"]
                status = f"{status} {pct:5.1f}%"
            if status != last:
                print("  " + status, end="\r" if "%" in status else "\n")
                last = status
    print("\nDone.")


if __name__ == "__main__":
    try:
        v = httpx.get(f"{config.OLLAMA_URL}/api/version", timeout=5).json()["version"]
    except Exception:
        sys.exit("Ollama is not running: open 'Ollama' from the Start menu, then run this again.")
    print(f"Ollama {v} is running.")
    pull()

    # One real flagged flight (AAL278 if Dawud's cycles are there)
    for i in range(len(replay_files())):
        aircraft, assessments, _ = assess_cycle(load_replay(i))
        flagged = [a for a in assessments if a.flagged]
        if flagged:
            a = flagged[0]
            cs = next(x.callsign for x in aircraft if x.icao24 == a.icao24)
            break
    else:
        sys.exit("No flagged flight in data/replay/.")
    d = fallback.decide_one(a, config.DEFAULT_THRESHOLD)
    print(f"\nTemplate : {writer.template_advisory(d, a, cs).text}")
    for attempt in ("1st call (loads the model)", "2nd call"):
        adv, imp = writer.granite_advisory(d, a, cs)
        print(f"\nGranite, {attempt}: {imp['latency_ms']:.0f} ms, {imp['energy_wh']} Wh, {imp['output_tokens']} tokens")
        print(f"  {adv.text}")
