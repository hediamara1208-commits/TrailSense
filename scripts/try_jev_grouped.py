"""Grouped vs one-by-one Jev calls on the same flights (task T2). Costs 4 Jev calls.
In VS Code: open this file, click Run > Run Python File in Dedicated Terminal.

Flights: the flagged flights of the recorded cycles in data/replay/ (AAL278, UAL46...) + the synthetic TEST350.
Prints each decision both ways, then calls / tokens / time: the frugality numbers for the receipt.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so that "backend" can be imported

from backend import config  # noqa: E402
from backend.agent import jev  # noqa: E402
from backend.physics.cycle import assess_cycle  # noqa: E402
from backend.sources.recorder import load_replay, replay_files  # noqa: E402
from scripts.try_jev import FLIGHT  # noqa: E402

if __name__ == "__main__":
    flights, callsigns = [], {"test01": "TEST350"}
    for i in range(len(replay_files())):
        aircraft, assessments, _ = assess_cycle(load_replay(i))
        names = {a.icao24: a.callsign for a in aircraft}
        for a in assessments:
            if a.flagged and jev.needs_jev(a):
                flights.append(a)
                callsigns[a.icao24] = names[a.icao24]
    flights.append(FLIGHT)
    print(f"{len(flights)} flights: {', '.join(callsigns[f.icao24] for f in flights)}\n")

    config.JEV_GROUPED = False
    single, u1 = jev.decide(flights, 0.8, callsigns)
    config.JEV_GROUPED = True
    grouped, u2 = jev.decide(flights, 0.8, callsigns)

    print(f"{'flight':<9}{'one by one':<32}{'grouped':<32}")
    for s, g in zip(single, grouped):
        fmt = lambda d: f"{d.action.value} {d.confidence:.2f} {d.route.value}"  # noqa: E731
        print(f"{callsigns[s.icao24]:<9}{fmt(s):<32}{fmt(g):<32}")
    print(f"\none by one: {u1['jev_calls']} calls, {u1['jev_input_tokens']} tokens, {u1['jev_ms']} ms")
    print(f"grouped:    {u2['jev_calls']} call(s), {u2['jev_input_tokens']} tokens, {u2['jev_ms']} ms "
          f"(grouped={u2['grouped']})")
