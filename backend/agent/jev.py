"""[HEDI] Jev = System 1: a fast, typed, calibrated decision for flagged flights.

SDK: pip install typesafe-sdk ; key in TYPESAFE_API_KEY ; model config.JEV_MODEL.
Raw API: POST https://api.typesafe.ai/v1/systemone  (Authorization: Bearer <key>)
Docs: https://docs.typesafe.ai/introduction/quickstart.md

Decision rule (validated in the playground, Fri 20 Nov, 23:40):
1. If NO option (climb or descend) has a positive net_benefit_co2e_kg,
   the code decides MAINTAIN directly, without calling Jev (always correct, free).
   Playground test TEST202: with every option negative, Jev still hesitated
   (maintain 43 %, descend 38 %), so this case is not left to Jev.
2. Otherwise we ask Jev the 4 QUESTIONS below. Jev does not compute anything: the state
   contains the numbers already computed by the physics (Dawud).
3. route = AUTO if confidence >= threshold, otherwise HUMAN (Sophie reviews).

Playground measurements (jev-1.14.0):
- TEST101 (descending is clearly better): descend_2000, confidence 0.97, 16 ms, 597 tokens in.
- TEST202 (all options negative): maintain, confidence 0.14 -> human review; 4 questions in 21 ms, 745 tokens.

Frugality to test: group several flagged flights into ONE request (one state for all flights,
questions prefixed by icao24), if the request size allows it.
"""
from backend.models import Decision, RiskAssessment

# The 4 questions, in the raw API / playground format (validated in the playground).
# With the Python SDK: Choice(instructions=..., criteria=...), Noul(...), Score(...).
QUESTIONS = {
    "action": {
        "type": "choice",
        "instructions": "Which altitude change should the dispatcher propose to avoid a warming contrail?",
        "criteria": {
            "climb_2000": "Climb 2,000 ft",
            "descend_2000": "Descend 2,000 ft",
            "maintain": "Keep the current level",
        },
    },
    "persistent_warming": {
        "type": "noul",
        "instructions": "If the flight stays at its current level, it will leave a persistent contrail "
                        "with a net warming effect.",
    },
    "forecast_reliability": {
        "type": "score",
        "instructions": "How reliable is the humidity forecast behind this recommendation?",
        "criteria": [
            "Low: humidity close to the 100% threshold or weak signal",
            "Medium: clear signal but model uncertainty noted",
            "High: strong, unambiguous signal",
        ],
    },
    "operational_feasibility": {
        "type": "score",
        "instructions": "How easy is the recommended change for the dispatcher and air traffic control to accept?",
        "criteria": [
            "Hard: large fuel cost or no clear benefit",
            "Possible: moderate cost",
            "Easy: small cost, standard altitude change",
        ],
    },
}


def needs_jev(assessment: RiskAssessment) -> bool:
    """True if at least one option (climb or descend) has a positive net benefit.

    Otherwise the decision is obvious (MAINTAIN) and we don't spend a Jev call.
    """
    return any(v > 0 for v in assessment.net_benefit_co2e_kg.values())


def build_state(assessment: RiskAssessment) -> str:
    """Compact JSON summary of the flight, in the format validated in the playground:
    flight, current_level (FL, heading, day/night), note "Do not recalculate",
    options {maintain_FLxxx, climb_to_FLyyy, descend_to_FLzzz} with RHi, persistence,
    extra fuel and net benefit, then the forecast quality."""
    raise NotImplementedError


def decide(assessments: list[RiskAssessment], threshold: float) -> tuple[list[Decision], dict]:
    """Decision for each flagged flight. Returns (decisions, usage) with
    usage = {calls, input_tokens, skipped_no_benefit}.

    - needs_jev() False -> Decision(action=MAINTAIN, confidence=1.0, route=AUTO), no call.
    - otherwise -> call Jev with build_state() + QUESTIONS, route by threshold.
    """
    raise NotImplementedError
