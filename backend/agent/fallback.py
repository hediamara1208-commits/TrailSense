"""[HEDI] Plan B without Jev: a hard-coded rule that takes over if the Jev API is down
or early access is blocked (config.USE_JEV = False, or an exception in jev.decide()).

Same input and output as jev.decide(), so pipeline.py can switch without changing anything else.

Proposed rule:
- Among climb and descend, keep the options whose level is NOT persistent.
- Pick the one with the largest net_benefit_co2e_kg, if it is positive.
- Otherwise: MAINTAIN.
- confidence = 1.0 at night with RHi > 110 %, otherwise 0.6 (so human review with the default threshold).
In the interface, clearly show "decision: fallback rule" to stay honest.
"""
from backend.models import Decision, RiskAssessment


def decide_by_rule(assessments: list[RiskAssessment], threshold: float) -> tuple[list[Decision], dict]:
    raise NotImplementedError
