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
import json
import os
import time

import httpx
from dotenv import load_dotenv

from backend import config
from backend.agent.fallback import route_for
from backend.models import Action, Decision, RiskAssessment

load_dotenv()  # TYPESAFE_API_KEY comes from .env (never committed)

API_URL = "https://api.typesafe.ai/v1/systemone"
TIMEOUT_S = 10.0

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


NOTE = ("All numbers were computed by a physics model. Do not recalculate them. "
        "A positive net_climate_benefit means the change avoids more warming than its extra fuel emits. "
        "Night contrails always warm the climate.")


def flight_state(assessment: RiskAssessment, callsign: str = "") -> dict:
    """The facts Jev needs about one flight: levels, humidity, persistence, fuel, net benefit, forecast margin."""
    a, cur = assessment, assessment.current

    def option(level, key: str | None) -> dict:
        return {
            "rhi_pct": round(level.rh_ice_pct),
            "contrail_forms": level.sac_satisfied,
            "persistent_contrail": level.persistent,
            "extra_fuel_kg": a.fuel_penalty_kg.get(key, 0) if key else 0,
            "net_climate_benefit_co2e_kg": a.net_benefit_co2e_kg.get(key, 0) if key else 0,
        }

    options = {f"maintain_FL{cur.flight_level}": option(cur, None)}
    if a.climb is not None:
        options[f"climb_to_FL{a.climb.flight_level}"] = option(a.climb, "climb")
    if a.descend is not None:
        options[f"descend_to_FL{a.descend.flight_level}"] = option(a.descend, "descend")
    margin = cur.rh_ice_pct - config.RHI_THRESHOLD
    return {
        "flight": callsign or a.icao24,
        "current_level": {"flight_level": cur.flight_level, "time": "night" if a.is_night else "day",
                          "minutes_in_ice_supersaturated_layer": a.minutes_in_issr},
        "options": options,
        "forecast": {"source": "GFS weather model (Open-Meteo), hourly",
                     "humidity_margin_above_persistence_threshold_pct": round(margin)},
    }


def build_state(assessment: RiskAssessment, callsign: str = "") -> str:
    """Compact JSON summary of ONE flight, in the format validated in the playground."""
    state = flight_state(assessment, callsign)
    state = {"flight": state["flight"], "current_level": state["current_level"], "note": NOTE,
             "options": state["options"], "forecast": state["forecast"]}
    return json.dumps(state, separators=(",", ":"))


def build_group_state(assessments: list[RiskAssessment], callsigns: dict[str, str]) -> str:
    """ONE state for several flights: the shared note once, then each flight keyed by its icao24."""
    flights = {a.icao24: flight_state(a, callsigns.get(a.icao24, "")) for a in assessments}
    return json.dumps({"note": NOTE, "flights": flights}, separators=(",", ":"))


def group_questions(assessments: list[RiskAssessment], callsigns: dict[str, str]) -> dict:
    """The 4 questions repeated per flight, ids prefixed by icao24 ("a32803__action")."""
    out = {}
    for a in assessments:
        who = f"For flight {callsigns.get(a.icao24) or a.icao24} (flights.{a.icao24} in the state): "
        for qid, q in QUESTIONS.items():
            out[f"{a.icao24}__{qid}"] = {**q, "instructions": who + q["instructions"]}
    return out


def _normalise_score(answer: dict, n_levels: int) -> float:
    """Jev returns a score on 0..(n_levels-1): bring it to 0-1."""
    return round(min(1.0, max(0.0, float(answer.get("score", 0)) / (n_levels - 1))), 3)


def parse_answers(assessment: RiskAssessment, answers: dict, threshold: float) -> Decision:
    """Raw API answers -> Decision. Kept separate so it can be tested without the network."""
    action = answers["action"]
    confidence = round(float(action.get("confidence", 0.0)), 3)
    forecast_reliability = _normalise_score(answers["forecast_reliability"],
                                            len(QUESTIONS["forecast_reliability"]["criteria"]))
    return Decision(
        icao24=assessment.icao24,
        action=Action(action["choice"]),
        confidence=confidence,
        persistent_warming_prob=round(float(answers["persistent_warming"].get("noul", 0.0)), 3),
        forecast_reliability=forecast_reliability,
        operational_feasibility=_normalise_score(answers["operational_feasibility"],
                                                 len(QUESTIONS["operational_feasibility"]["criteria"])),
        route=route_for(confidence, threshold, forecast_reliability, action["choice"]),
        decided_by="jev",
        probabilities={k: round(float(v), 3) for k, v in action.get("probabilities", {}).items()},
    )


def _post(client: httpx.Client, state: str, questions: dict, usage: dict) -> dict:
    body = {"model": config.JEV_MODEL, "state": state, "questions": questions}
    t0 = time.perf_counter()
    r = client.post(API_URL, json=body)
    usage["jev_ms"] += (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    data = r.json()
    usage["jev_calls"] += 1
    usage["jev_input_tokens"] += data.get("usage", {}).get("input_tokens", 0)
    return data["answers"]


def decide(assessments: list[RiskAssessment], threshold: float,
           callsigns: dict[str, str] | None = None) -> tuple[list[Decision], dict]:
    """Jev decision for each flight that needs it (needs_jev() is checked by pipeline.py first).

    With config.JEV_GROUPED: one request per group of up to JEV_MAX_GROUP flights; if a grouped
    call fails or misses an answer, that group is retried one flight per call.
    Returns (decisions, usage) with usage = {jev_calls, jev_input_tokens, jev_ms, grouped}.
    Any other error (no key, network, quota) is raised: pipeline.py then switches to the fallback rule.
    """
    key = os.getenv("TYPESAFE_API_KEY")
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY missing from .env")
    callsigns = callsigns or {}
    decisions: list[Decision] = []
    usage = {"jev_calls": 0, "jev_input_tokens": 0, "jev_ms": 0.0, "grouped": False}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=TIMEOUT_S, headers=headers) as client:
        singles = list(assessments)
        if config.JEV_GROUPED and len(assessments) > 1:
            singles = []
            size = max(1, config.JEV_MAX_GROUP)
            for start in range(0, len(assessments), size):
                group = assessments[start:start + size]
                try:
                    answers = _post(client, build_group_state(group, callsigns),
                                    group_questions(group, callsigns), usage)
                    for a in group:
                        mine = {qid: answers[f"{a.icao24}__{qid}"] for qid in QUESTIONS}
                        decisions.append(parse_answers(a, mine, threshold))
                    usage["grouped"] = True
                except (httpx.HTTPStatusError, KeyError, ValueError):
                    singles += group   # too big or malformed: retry these one by one
        for a in singles:
            answers = _post(client, build_state(a, callsigns.get(a.icao24, "")), QUESTIONS, usage)
            decisions.append(parse_answers(a, answers, threshold))
    usage["jev_ms"] = round(usage["jev_ms"], 1)
    return decisions, usage
