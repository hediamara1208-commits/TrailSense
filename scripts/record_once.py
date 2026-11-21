"""Records ONE cycle of the real sky (OpenSky aircraft + Open-Meteo weather over the BBOX)
into data/replay/<timestamp>.json. In VS Code: open this file, click Run (top-right).

Useful to test Replay mode without the overnight recorder (sources/recorder.py run_forever).
Uses OPENSKY_CLIENT_ID / OPENSKY_CLIENT_SECRET from .env if present, otherwise anonymous access.
"""
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so that "backend" can be imported

from backend.sources.recorder import record_cycle  # noqa: E402

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    path = record_cycle(with_weather=True)
    print(f"\nRecorded: {path}" if path else "\nNothing recorded (OpenSky returned no aircraft: rate limit or network).")
