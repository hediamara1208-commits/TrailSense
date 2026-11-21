"""[HEDI] Plan B without Jev: a hard-coded rule that takes over if the Jev API is down
or early access is blocked (config.USE_JEV = False, or an exception in jev.decide()).

Same input and output as jev.decide(), so pipeline.py can switch without changing anything else.

Rule:
- Among climb and descend, keep the options whose level is NOT persistent.
- Pick the one with the largest net_benefit_co2e_kg, if it is positive. Otherwise: MAINTAIN.
- confidence = 1.0 at night with RHi > 110 %, otherwise 0.6 (so human review with the default threshold).
The other three scores are rough rule-of-thumb estimates (not Jev outputs).
In the interface, decided_by = "rule" is shown, to stay honest.
"""
from backend.models import Action, Decision, RiskAssessment, Route

CONFIDENT_RHI = 110.0      # RHi (%) above which the layer is clearly supersaturated
EASY_FUEL_KG = 50.0        # extra fuel below which the change is considered easy

_ACTIONS = {"climb": Action.CLIMB, "descend": Action.DESCEND}


def route_for(confidence: float, threshold: float) -> Route:
    """The autonomy threshold: AUTO if confident enough, otherwise Sophie reviews."""
    return Route.AUTO if confidence >= threshold else Route.HUMAN


def best_option(a: RiskAssessment) -> str | None:
    """'climb' or 'descend' with the largest positive net benefit at a non-persistent level, else None."""
    candidates = [name for name, level in (("climb", a.climb), ("descend", a.descend))
                  if level is not None and not level.persistent and a.net_benefit_co2e_kg.get(name, 0) > 0]
    return max(candidates, key=lambda n: a.net_benefit_co2e_kg[n], default=None)


def decide_one(a: RiskAssessment, threshold: float) -> Decision:
    option = best_option(a)
    clear_signal = a.current.rh_ice_pct > CONFIDENT_RHI
    confidence = 1.0 if (a.is_night and clear_signal) else 0.6
    fuel = a.fuel_penalty_kg.get(option, 0.0) if option else 0.0
    return Decision(
        icao24=a.icao24,
        action=_ACTIONS[option] if option else Action.MAINTAIN,
        confidence=confidence,
        persistent_warming_prob=0.9 if a.is_night else 0.6,   # night contrails always warm
        forecast_reliability=1.0 if clear_signal else 0.5,
        operational_feasibility=1.0 if fuel < EASY_FUEL_KG else 0.5,
        route=route_for(confidence, threshold),
        decided_by="rule",
    )


def decide_by_rule(assessments: list[RiskAssessment], threshold: float) -> tuple[list[Decision], dict]:
    """Same signature as jev.decide(): (decisions, usage). The rule costs nothing."""
    return [decide_one(a, threshold) for a in assessments], {"jev_calls": 0, "jev_input_tokens": 0}


def maintain_by_physics(a: RiskAssessment) -> Decision:
    """No option has a positive net benefit: MAINTAIN is obvious, decided in code without Jev."""
    return Decision(icao24=a.icao24, action=Action.MAINTAIN, confidence=1.0,
                    persistent_warming_prob=0.9 if a.is_night else 0.6,
                    forecast_reliability=1.0, operational_feasibility=1.0,
                    route=Route.AUTO, decided_by="physics")
