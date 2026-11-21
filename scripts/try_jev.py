"""ONE real Jev call on a synthetic humid night flight (the real sky may be dry).
In VS Code: open this file, click Run > Run Python File in Dedicated Terminal.

Reads TYPESAFE_API_KEY from .env (never printed). Costs one Jev call (~600 tokens).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so that "backend" can be imported

from backend import config  # noqa: E402
from backend.agent import jev  # noqa: E402
from backend.models import LevelRisk, RiskAssessment  # noqa: E402

FLIGHT = RiskAssessment(
    icao24="test01",
    current=LevelRisk(350, -60.3, 125.0, True, True),    # FL350: persistent contrail
    climb=LevelRisk(370, -62.0, 80.0, True, False),       # FL370: dry, no persistent contrail
    descend=LevelRisk(330, -56.0, 120.0, True, True),     # FL330: still humid
    is_night=True, flagged=True, minutes_in_issr=12.0,
    fuel_penalty_kg={"climb": 23.3, "descend": 31.0},
    warming_avoided_co2e_kg={"climb": 900.0, "descend": 0.0},
    net_benefit_co2e_kg={"climb": 826.0, "descend": -98.0},
)

if __name__ == "__main__":
    state = jev.build_state(FLIGHT, "TEST350")
    print(f"Model: {config.JEV_MODEL} · state: {len(state)} characters")
    print(state, "\n")
    decisions, usage = jev.decide([FLIGHT], threshold=config.DEFAULT_THRESHOLD, callsigns={"test01": "TEST350"})
    d = decisions[0]
    print(f"Decision: {d.action.value} · confidence {d.confidence} -> {d.route.value}")
    print(f"persistent_warming {d.persistent_warming_prob} · forecast_reliability {d.forecast_reliability} · "
          f"feasibility {d.operational_feasibility}")
    print(f"Usage: {usage}")
    print("\nExpected: climb_2000 (only climbing avoids the layer, at a positive net benefit).")
